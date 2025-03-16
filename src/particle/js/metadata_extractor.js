const path = require('path');
const fs = require('fs');

function extractMetadata(ast, code, filePath, rich = false) {
  const fileExt = path.extname(filePath);
  let particle = {
    path: path.relative('/project', filePath),
    type: fileExt === '.jsx' || fileExt === '.tsx' ? 'component' : 'file',
    purpose: `Handles ${path.basename(filePath, fileExt).toLowerCase()} functionality`,
    props: [],
    hooks: [],
    calls: [],
    logic: [],
    depends_on: [],
    jsx: [],
    state_machine: null,
    routes: [],
    comments: [],
    used_by: [],
    core_rules: [], // Highlight app-defining rules
    references: { hooks: {}, calls: {}, routes: {} } // Map to files/lines for AI/devs
  };

  // Comments (unchanged)
  if (ast.comments && ast.comments.length > 0) {
    ast.comments.forEach((comment) => {
      const text = comment.value.trim().replace(/^\*+\s*/gm, '').replace(/\n\s*\*\s*/g, '\n');
      if (text.toLowerCase().includes('todo') || text.toLowerCase().includes('fixme')) {
        particle.comments.push({ type: 'todo', text });
      } else if (comment.type === 'CommentBlock' && comment.loc.start.line <= 20) {
        particle.comments.push({ type: 'doc', text });
        if (text.includes('component') || text.includes('Component')) {
          particle.purpose = text.split('\n')[0].trim();
        }
      }
    });
  }

  function walk(node) {
    if (!node) return;

    // Imports
    if (node.type === 'ImportDeclaration') {
      const source = node.source.value;
      const specifiers = node.specifiers
        .map((spec) =>
          spec.type === 'ImportDefaultSpecifier' ? spec.local.name : spec.imported?.name || null
        )
        .filter(Boolean);
      particle.depends_on.push({ source, specifiers: specifiers.length > 0 ? specifiers : null });
      console.error(`Found import: ${source}`);
    }

    // Hooks and Calls
    if (node.type === 'CallExpression') {
      const callee =
        node.callee.name ||
        (node.callee.property && `${node.callee.object?.name}.${node.callee.property.name}`);
      if (callee?.startsWith('use')) {
        particle.hooks.push(callee);
        particle.references.hooks[callee] = { line: node.loc.start.line };
      }
      if (callee === 'fetch' || ['axios', 'supabase'].includes(node.callee.object?.name) || callee?.includes('router')) {
        particle.calls.push(callee);
        particle.references.calls[callee] = { line: node.loc.start.line };
      }
    }

    // Routes from router.push/replace
    if (node.type === 'ExpressionStatement' && node.expression?.callee?.property?.name === 'replace') {
      const route = node.expression.arguments[0]?.value;
      if (route) {
        particle.routes.push(route);
        particle.references.routes[route] = { line: node.loc.start.line };
      }
    }

    for (const key in node) if (node[key] && typeof node[key] === 'object') walk(node[key]);
  }

  function enhanceWalk(node) {
    if (!node) return;

    if (node.type === 'IfStatement' && node.test) {
      // Extract condition
      let condition = '';
      if (node.test.type === 'Identifier') {
        condition = node.test.name;
      } else if (node.test.type === 'UnaryExpression' && node.test.operator === '!') {
        if (node.test.argument?.type === 'CallExpression' && node.test.argument.callee?.property?.name === 'includes') {
          const arg = node.test.argument.arguments[0];
          condition = `!${arg?.name || arg?.value || 'check'}.includes`;
        }
      } else if (node.test.type === 'BinaryExpression') {
        condition = `${node.test.left?.name || node.test.left?.value || ''} ${node.test.operator} ${node.test.right?.name || node.test.right?.value || ''}`;
      } else if (node.test.type === 'LogicalExpression') {
        condition = `${node.test.left?.name || 'condition'} ${node.test.operator} ${node.test.right?.name || 'condition'}`;
      }

      if (condition) {
        // Extract action
        let action = 'handles condition';
        if (node.consequent.type === 'BlockStatement') {
          node.consequent.body.forEach((stmt) => {
            if (stmt.type === 'ExpressionStatement' && stmt.expression?.type === 'CallExpression') {
              const callee =
                stmt.expression.callee?.name ||
                (stmt.expression.callee?.property?.name &&
                  `${stmt.expression.callee.object?.name}.${stmt.expression.callee.property.name}`);
              if (callee === 'console.error') {
                action = 'logs error';
              } else if (callee?.includes('router')) {
                action = `redirects to ${stmt.expression.arguments[0]?.value || 'route'}`;
              } else if (callee) {
                action = `calls ${callee}`;
              }
            } else if (stmt.type === 'VariableDeclaration') {
              action = 'sets variable';
            }
          });
        }

        const logicEntry = { condition, action, line: node.loc.start.line };
        particle.logic.push(logicEntry);

        // Tag core rules (e.g., capacity, stage, auth, routing)
        if (
          condition.includes('capacity') || 
          action.includes('stage') || 
          action.includes('redirect') || 
          condition.includes('role') || 
          condition.includes('isAuthenticated')
        ) {
          particle.core_rules.push(logicEntry);
        }
      }
    }

    for (const key in node) if (node[key] && typeof node[key] === 'object') enhanceWalk(node[key]);
  }

  walk(ast.program);
  if (rich) enhanceWalk(ast.program);

  // Merge with existing Particle
  const existingMatch = code.match(/export const Particle = \{[\s\S]*?\};/);
  if (existingMatch) {
    try {
      const cleanedCode = existingMatch[0].replace('export const Particle =', '').trim().replace(/;$/, '');
      const existing = eval(`(${cleanedCode})`);
      particle.purpose = existing.purpose || particle.purpose;
      ['props', 'hooks', 'calls', 'logic', 'depends_on', 'jsx', 'routes', 'comments', 'core_rules'].forEach((field) => {
        if (existing[field]) {
          if (typeof existing[field][0] !== 'object') {
            particle[field] = [...new Set([...(existing[field] || []), ...particle[field]])];
          } else {
            const merged = [...existing[field]];
            particle[field].forEach((item) => {
              if (!merged.some((m) => JSON.stringify(m) === JSON.stringify(item))) merged.push(item);
            });
            particle[field] = merged;
          }
        }
      });
    } catch (e) {
      console.error(`Failed to parse existing Particle in ${filePath}: ${e.message}`);
    }
  }

  // Filter empty fields
  Object.keys(particle).forEach((key) => {
    if (Array.isArray(particle[key]) && particle[key].length === 0) delete particle[key];
    if (key === 'state_machine' && (!particle[key] || (particle[key].states && particle[key].states.length === 0)))
      delete particle[key];
  });

  return particle;
}

if (require.main === module) {
  const filePath = process.argv[2];
  if (!filePath) {
    console.error('No file path provided');
    process.exit(1);
  }
  let astInput = '';
  process.stdin
    .setEncoding('utf8')
    .on('data', (chunk) => (astInput += chunk))
    .on('end', () => {
      try {
        const ast = JSON.parse(astInput);
        const absolutePath = filePath.startsWith('/project/') ? filePath : path.join('/project', filePath);
        const code = fs.readFileSync(absolutePath, 'utf-8');
        const rich = process.env.RICH_PARSING === '1';
        const particle = extractMetadata(ast, code, filePath, rich);
        console.log(JSON.stringify(particle));
      } catch (error) {
        console.error(`Error processing ${filePath}: ${error.message}`);
        process.exit(1);
      }
    });
}

module.exports = { extractMetadata };