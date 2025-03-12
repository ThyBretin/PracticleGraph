const { parse } = require('@babel/parser');
const fs = require('fs');
const path = require('path');

const filePath = process.argv[2];
if (!filePath) {
  console.error('No file path provided');
  process.exit(1);
}

try {
  let absolutePath = filePath.startsWith('/project/') ? filePath : path.join('/project', filePath);
  console.error(`Reading file from: ${absolutePath}`);
  const code = fs.readFileSync(absolutePath, 'utf-8');
  const ast = parse(code, {
    sourceType: 'module',
    plugins: ['jsx', 'flow']
  });

  let props = [];
  let hooks = [];
  let calls = [];
  let keyLogic = [];
  let dependsOn = [];
  let jsx = [];
  let purpose = `Handles ${path.basename(absolutePath).replace(/\.(jsx|js)$/, '').toLowerCase()} functionality`;

  function walk(node) {
    if (!node) return;

    if (node.type === 'FunctionDeclaration' || node.type === 'ArrowFunctionExpression') {
      const name = node.id?.name || (node.parent?.id?.name && absolutePath.endsWith(`${node.parent.id.name}.jsx`));
      if (name && (absolutePath.endsWith(`${name}.jsx`) || absolutePath.endsWith(`${name}.js`))) {
        if (node.params[0]?.type === 'ObjectPattern') {
          props = node.params[0].properties.map(p => p.key.name);
        } else if (node.params[0]?.type === 'Identifier') {
          props = [node.params[0].name];
        }
      }
    }

    if (node.type === 'CallExpression') {
      const callee = node.callee.name || (node.callee.property && `${node.callee.object.name}.${node.callee.property.name}`);
      if (callee?.startsWith('use')) hooks.push(callee);
      if (callee === 'fetch' || node.callee.object?.name === 'supabase') calls.push(callee);
    }

    if (node.type === 'ImportDeclaration') {
      dependsOn.push(node.source.value);
      if (node.source.value === 'react-native') {
        node.specifiers.forEach(spec => {
          if (spec.imported?.name === 'ScrollView') keyLogic.push('Responds to scroll events');
          if (spec.imported?.name === 'FlatList') keyLogic.push('Renders list-based UI');
        });
      }
    }

    for (const key in node) if (node[key] && typeof node[key] === 'object') walk(node[key]);
  }

  function enhanceWalk(node, subParticle) {
    if (!node) return;

    if (node.type === 'VariableDeclarator' && node.init?.callee?.name?.startsWith('use')) {
      if (node.id?.type === 'ObjectPattern') {
        props.push(...node.id.properties.map(p => p.key.name));
      }
    }

    if (node.type === 'CallExpression') {
      const callee = node.callee.name || (node.callee.property && `${node.callee.object.name}.${node.callee.property.name}`);
      if (callee) {
        if (callee === 'router.push' || callee === 'navigateToTab') {
          const arg = node.arguments[0]?.value;
          calls.push(arg ? `${callee}('${arg}')` : callee);
        } else if (['withSpring', 'withTiming', 'setVisibilityAsync', 'setBackgroundColorAsync'].includes(callee.split('.').pop())) {
          calls.push(callee);
        }
      }
    }

    if (node.type === 'JSXElement') {
      const tag = node.openingElement?.name?.name;
      if (tag) {
        const handlers = node.openingElement.attributes
          ?.filter(attr => attr.name?.name?.startsWith('on'))
          ?.map(attr => attr.name.name) || [];
        const entry = `${handlers.length > 0 ? `${handlers.join(', ')} on ` : ''}${tag}`;
        if (!jsx.includes(entry)) jsx.push(entry);
      }
    }

    if (node.type === 'IfStatement') {
      const test = node.test;
      let condition = '';
      if (test?.type === 'Identifier') condition = test.name;
      else if (test?.type === 'BinaryExpression') {
        const left = test.left?.property ? `${test.left.object?.name}.${test.left.property.name}` : (test.left?.name || test.left?.value);
        const right = test.right?.property ? `${test.right.object?.name}.${test.right.property.name}` : (test.right?.name || test.right?.value);
        condition = `${left || 'unknown'} ${test.operator} ${right || 'unknown'}`;
      }
      if (condition && !condition.includes('unknown')) keyLogic.push(`if on \`${condition}\``);
    }
    if (node.type === 'ConditionalExpression') {
      const test = node.test;
      let condition = '';
      if (test?.type === 'Identifier') condition = test.name;
      else if (test?.type === 'BinaryExpression') {
        const left = test.left?.name || test.left?.value;
        const right = test.right?.name || test.right?.value;
        condition = `${left || 'unknown'} ${test.operator} ${right || 'unknown'}`;
      }
      if (condition && !condition.includes('unknown')) keyLogic.push(`if on \`${condition}\``);
    }
    if (node.type === 'CallExpression' && node.callee?.property?.name === 'map') {
      const array = node.callee.object?.name || 'data';
      keyLogic.push(`maps \`${array}\``);
    }
    if (node.type === 'AssignmentExpression') {
      const left = node.left?.name || (node.left?.property && `${node.left.object?.name}.${node.left.property.name}`);
      if (left) keyLogic.push(`sets \`${left}\``);
    }
    if (node.type === 'CallExpression' && ['withSpring', 'withTiming'].includes(node.callee?.name)) {
      const target = node.arguments[0]?.properties?.find(p => p.key?.name === 'transform')?.value?.elements?.[0]?.properties?.[0]?.key?.name;
      keyLogic.push(`animates \`${target || 'UI'}\` with ${node.callee.name}`);
    }
    if (node.type === 'ArrowFunctionExpression' && node.body?.type === 'BlockStatement' && node.body?.directives?.some(d => d.value?.value === 'worklet')) {
      node.body.body?.forEach(statement => {
        if (statement.type === 'VariableDeclaration' && statement.declarations[0]?.init?.type === 'LogicalExpression') {
          const left = statement.declarations[0].init.left;
          const right = statement.declarations[0].init.right;
          const leftCond = left?.left?.name && left?.right?.value ? `${left.left.name} ${left.operator} ${left.right.value}` : '';
          const rightCond = right?.left?.name && right?.right?.value ? `${right.left.name} ${right.operator} ${right.right.value}` : '';
          const condition = [leftCond, rightCond].filter(Boolean).join(' || ');
          if (condition) keyLogic.push(`if on \`${condition}\``);
        }
      });
    }

    for (const key in node) if (node[key] && typeof node[key] === 'object') walk(node[key]);
  }

  walk(ast);
  if (process.env.RICH_PARSING) enhanceWalk(ast, { props, hooks, calls, keyLogic, jsx });

  const existingMatch = code.match(/export const SubParticle = \{[\s\S]*?\};/);
  let existing = {};
  if (existingMatch) {
    try {
      const cleanedCode = existingMatch[0].replace('export const SubParticle =', '').trim().replace(/;$/, '');
      existing = eval(`(${cleanedCode})`);
      purpose = existing.purpose || purpose;
      props = [...new Set([...(existing.props || []), ...props])];
      hooks = [...new Set([...(existing.hooks || []), ...hooks])];
      calls = [...new Set([...(existing.calls || []), ...calls])];
      keyLogic = [...new Set([...(existing.key_logic || []), ...keyLogic])];
      dependsOn = [...new Set([...(existing.depends_on || []), ...dependsOn])];
      jsx = [...new Set([...(existing.jsx || []), ...jsx])];
    } catch (e) {
      console.error(`Failed to parse existing SubParticle in ${filePath}: ${e.message}`);
    }
  }

  const subParticle = {
    purpose,
    props: props.filter(Boolean),
    hooks: [...new Set(hooks)],
    calls: [...new Set(calls)],
    key_logic: [...new Set(keyLogic)],
    depends_on: [...new Set(dependsOn)],
    ...(process.env.RICH_PARSING && { jsx: [...new Set(jsx)] })
  };

  console.log(JSON.stringify(subParticle, null, 2)); // Pretty-print for safety
} catch (error) {
  console.error(`Error parsing ${filePath}: ${error.message}`);
  process.exit(1);
}