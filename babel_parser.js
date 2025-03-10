const { parse } = require('@babel/parser');
const fs = require('fs');
const path = require('path');

const filePath = process.argv[2];
if (!filePath) {
  console.error('No file path provided');
  process.exit(1);
}

try {
  // Handle both absolute paths (starting with /project) and relative paths
  let absolutePath;
  if (filePath.startsWith('/project/')) {
    absolutePath = filePath;
  } else {
    absolutePath = path.join('/project', filePath);
  }
  
  console.error(`Reading file from: ${absolutePath}`); // Debug log
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

    if (node.type === 'IfStatement') keyLogic.push('Branches on conditions');
    if (node.type === 'ForStatement' || node.type === 'CallExpression' && node.callee.property?.name === 'map') {
      keyLogic.push('Iterates over data');
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

  walk(ast);

  const existingMatch = code.match(/export const SubParticule = \{[\s\S]*?\};/);
  let existing = {};
  if (existingMatch) {
    try {
      // Clean up trailing semicolon and eval safely
      const cleanedCode = existingMatch[0].replace('export const SubParticule =', '').trim().replace(/;$/, '');
      existing = eval(`(${cleanedCode})`);
      purpose = existing.purpose || purpose;
      props = [...new Set([...existing.props || [], ...props])];
      hooks = [...new Set([...existing.hooks || [], ...hooks])];
      calls = [...new Set([...existing.calls || [], ...calls])];
      keyLogic = [...new Set([...existing.key_logic || [], ...keyLogic])];
      dependsOn = [...new Set([...existing.depends_on || [], ...dependsOn])];
    } catch (e) {
      console.error(`Failed to parse existing SubParticule: ${e.message}`);
    }
  }

  const subParticule = {
    purpose,
    props: props.filter(Boolean),
    hooks: [...new Set(hooks)],
    calls: [...new Set(calls)],
    key_logic: [...new Set(keyLogic)],
    depends_on: [...new Set(dependsOn)]
  };

  console.log(JSON.stringify(subParticule));
} catch (error) {
  console.error(`Error parsing ${filePath}: ${error.message}`);
  process.exit(1);
}