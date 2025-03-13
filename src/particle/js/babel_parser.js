const { parse } = require('@babel/parser');
const fs = require('fs');
const path = require('path');

const filePath = process.argv[2];
if (!filePath) {
  console.error('No file path provided');
  process.exit(1);
}

try {
  const absolutePath = filePath.startsWith('/project/') ? filePath : path.join('/project', filePath);
  console.error(`Reading file from: ${absolutePath}`);
  const code = fs.readFileSync(absolutePath, 'utf-8');
  const ast = parse(code, {
    sourceType: 'module',
    plugins: ['jsx', 'flow']
  });

  const fileExt = path.extname(absolutePath);
  let particle = {
    path: path.relative('/project', absolutePath),
    type: fileExt === '.jsx' ? 'component' : 'file',
    purpose: `Handles ${path.basename(absolutePath, fileExt).toLowerCase()} functionality`,
    props: [],
    hooks: [],
    calls: [],
    logic: [],
    depends_on: [],
    jsx: [],
    state_machine: null,
    used_by: [] // Placeholder—needs dependency_tracker.py
  };

  function walk(node) {
    if (!node) return;

    // Props (top-level functions only, with defaults)
    if ((node.type === 'FunctionDeclaration' || node.type === 'ArrowFunctionExpression') && node.loc?.start.line <= 10) {
      node.params.forEach(param => {
        if (param.type === 'ObjectPattern') {
          particle.props = param.properties.map(p => ({
            name: p.key.name,
            default: p.value?.type === 'AssignmentPattern' ? 
              (p.value.right.value ?? p.value.right.name ?? null) : null
          }));
        } else if (param.type === 'Identifier') {
          particle.props = [{ name: param.name, default: null }];
        }
      });
    }

    // Hooks
    if (node.type === 'CallExpression') {
      const callee = node.callee.name || (node.callee.property && `${node.callee.object.name}.${node.callee.property.name}`);
      if (callee?.startsWith('use')) particle.hooks.push(callee);
      if (callee === 'fetch' || node.callee.object?.name === 'supabase') particle.calls.push(callee);
    }

    // Depends On (imports)
    if (node.type === 'ImportDeclaration') {
      particle.depends_on.push(node.source.value);
    }

    // Recurse
    for (const key in node) if (node[key] && typeof node[key] === 'object') walk(node[key]);
  }

  function enhanceWalk(node) {
    if (!node) return;

    // Rich Props (from hooks destructuring)
    if (node.type === 'VariableDeclarator' && node.init?.callee?.name?.startsWith('use')) {
      if (node.id?.type === 'ObjectPattern') {
        node.id.properties.forEach(p => {
          const existing = particle.props.find(prop => prop.name === p.key.name);
          if (!existing) particle.props.push({ name: p.key.name, default: null });
        });
      }
    }

    // Calls (navigation + animations)
    if (node.type === 'CallExpression') {
      const callee = node.callee.name || (node.callee.property && `${node.callee.object.name}.${node.callee.property.name}`);
      if (callee) {
        if (callee === 'router.push' || callee === 'navigateToTab') {
          const arg = node.arguments[0]?.value;
          particle.calls.push(arg ? `${callee}('${arg}')` : callee);
        } else if (['withSpring', 'withTiming'].includes(callee)) {
          particle.calls.push(callee);
        }
      }
    }

    // JSX
    if (node.type === 'JSXElement') {
      const tag = node.openingElement?.name?.name;
      if (tag) {
        const handlers = node.openingElement.attributes
          ?.filter(attr => attr.name?.name?.startsWith('on'))
          ?.map(attr => attr.name.name) || [];
        particle.jsx.push(`${handlers.length > 0 ? `${handlers.join(', ')} on ` : ''}${tag}`);
      }
    }

    // Logic (conditions + detailed actions)
    if (node.type === 'IfStatement') {
      const test = node.test;
      let condition = '';
      if (test?.type === 'Identifier') condition = test.name;
      else if (test?.type === 'BinaryExpression') {
        const left = test.left?.property ? `${test.left.object?.name}.${test.left.property.name}` : (test.left?.name || test.left?.value);
        const right = test.right?.property ? `${test.right.object?.name}.${test.right.property.name}` : (test.right?.name || test.right?.value);
        condition = `${left || 'unknown'} ${test.operator} ${right || 'unknown'}`;
      }
      if (condition && !condition.includes('unknown')) {
        let action = 'handles condition';
        if (node.consequent.type === 'BlockStatement') {
          node.consequent.body.forEach(stmt => {
            if (stmt.type === 'ReturnStatement' && stmt.argument?.type === 'JSXElement') {
              action = `renders ${stmt.argument.openingElement.name.name}`;
            } else if (stmt.type === 'ExpressionStatement' && stmt.expression?.callee?.name === 'router.push') {
              action = `navigates to ${stmt.expression.arguments[0]?.value || 'route'}`;
            }
          });
        }
        particle.logic.push(`if ${condition} ${action}`);
      }
    }

    // State Machines (e.g., EVENT_STATES)
    if (node.type === 'VariableDeclarator' && node.id.name?.endsWith('_STATES')) {
      particle.state_machine = {
        name: node.id.name,
        states: node.init?.properties?.map(prop => ({
          name: prop.key.name,
          transitions: [] // Placeholder—needs deeper parsing
        })) || []
      };
    }

    // Recurse
    for (const key in node) if (node[key] && typeof node[key] === 'object') enhanceWalk(node[key]);
  }

  walk(ast);
  if (process.env.RICH_PARSING) enhanceWalk(ast);

  // Merge with existing Particle
  const existingMatch = code.match(/export const Particle = \{[\s\S]*?\};/);
  if (existingMatch) {
    try {
      const cleanedCode = existingMatch[0].replace('export const Particle =', '').trim().replace(/;$/, '');
      const existing = eval(`(${cleanedCode})`);
      particle.purpose = existing.purpose || particle.purpose;
      particle.props = [...new Set([...(existing.props || []), ...particle.props])];
      particle.hooks = [...new Set([...(existing.hooks || []), ...particle.hooks])];
      particle.calls = [...new Set([...(existing.calls || []), ...particle.calls])];
      particle.logic = [...new Set([...(existing.logic || existing.key_logic || []), ...particle.logic])];
      particle.depends_on = [...new Set([...(existing.depends_on || []), ...particle.depends_on])];
      particle.jsx = [...new Set([...(existing.jsx || []), ...particle.jsx])];
      particle.state_machine = existing.state_machine || particle.state_machine;
    } catch (e) {
      console.error(`Failed to parse existing Particle in ${filePath}: ${e.message}`);
    }
  }

  // Filter empty fields
  Object.keys(particle).forEach(key => {
    if (Array.isArray(particle[key]) && particle[key].length === 0) delete particle[key];
    if (key === 'state_machine' && (!particle[key] || particle[key].states.length === 0)) delete particle[key];
  });

  console.log(JSON.stringify(particle, null, 2));
} catch (error) {
  console.error(`Error parsing ${filePath}: ${error.message}`);
  process.exit(1);
}