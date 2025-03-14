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
  
  // Determine if the file has TypeScript content (simple heuristic)
  const hasTypeScriptSyntax = code.includes(': ') || code.includes('<T>') || 
                              code.includes('interface ') || code.includes('type ') ||
                              absolutePath.endsWith('.ts') || absolutePath.endsWith('.tsx');
  
  // Configure plugins based on content and file extension
  const plugins = ['jsx', 'decorators-legacy'];
  if (hasTypeScriptSyntax) {
    plugins.push('typescript');
  } else {
    plugins.push('flow');
  }
  
  const ast = parse(code, {
    sourceType: 'module',
    plugins: plugins,
    tokens: true,
    comments: true
  });

  const fileExt = path.extname(absolutePath);
  let particle = {
    path: path.relative('/project', absolutePath),
    type: fileExt === '.jsx' || fileExt === '.tsx' ? 'component' : 'file',
    purpose: `Handles ${path.basename(absolutePath, fileExt).toLowerCase()} functionality`,
    props: [],
    hooks: [],
    calls: [],
    logic: [],
    depends_on: [],
    jsx: [],
    state_machine: null,
    routes: [],
    comments: [],
    used_by: [] // Placeholder—needs dependency_tracker.py
  };

  // Extract comments - this will include documentation and TODOs
  if (ast.comments && ast.comments.length > 0) {
    ast.comments.forEach(comment => {
      // Clean multiline comments
      const text = comment.value.trim()
        .replace(/^\*+\s*/gm, '') // Remove leading asterisks
        .replace(/\n\s*\*\s*/g, '\n'); // Clean multiline format
      
      if (text.toLowerCase().includes('todo') || text.toLowerCase().includes('fixme')) {
        particle.comments.push({ type: 'todo', text, line: comment.loc.start.line });
      } else if (comment.type === 'CommentBlock' && comment.loc.start.line <= 20) {
        // Likely a file or component description
        particle.comments.push({ type: 'doc', text, line: comment.loc.start.line });
        
        // If it seems like a component description, update the purpose
        if (text.includes('component') || text.includes('Component')) {
          particle.purpose = text.split('\n')[0].trim();
        }
      }
    });
  }

  function walk(node) {
    if (!node) return;

    // Props (top-level functions only, with defaults)
    if ((node.type === 'FunctionDeclaration' || node.type === 'ArrowFunctionExpression') && node.loc?.start.line <= 10) {
      node.params.forEach(param => {
        if (param.type === 'ObjectPattern') {
          particle.props = param.properties.map(p => ({
            name: p.key.name,
            default: p.value?.type === 'AssignmentPattern' ? 
              (p.value.right.value ?? p.value.right.name ?? null) : null,
            required: p.value?.type !== 'AssignmentPattern'
          }));
        } else if (param.type === 'Identifier') {
          particle.props = [{ name: param.name, default: null, required: true }];
        }
      });
    }

    // Hooks
    if (node.type === 'CallExpression') {
      const callee = node.callee.name || (node.callee.property && `${node.callee.object?.name}.${node.callee.property.name}`);
      if (callee?.startsWith('use')) {
        const args = node.arguments.map(arg => {
          if (arg.type === 'StringLiteral' || arg.type === 'NumericLiteral') return arg.value;
          if (arg.type === 'Identifier') return arg.name;
          if (arg.type === 'ObjectExpression') return '{...}';
          if (arg.type === 'ArrayExpression') return '[...]';
          return null;
        }).filter(Boolean);
        
        particle.hooks.push({
          name: callee,
          args: args.length > 0 ? args : null,
          line: node.loc.start.line
        });
      }
      
      // API calls and other important function calls
      if (callee === 'fetch' || 
          (node.callee.object?.name === 'axios') ||
          (node.callee.object?.name === 'supabase')) {
        const args = node.arguments.map(arg => {
          if (arg.type === 'StringLiteral') return arg.value;
          return null;
        }).filter(Boolean);
        
        particle.calls.push({
          name: callee,
          args: args.length > 0 ? args : null,
          line: node.loc.start.line
        });
      }
    }

    // Depends On (imports)
    if (node.type === 'ImportDeclaration') {
      const source = node.source.value;
      const specifiers = node.specifiers.map(spec => {
        if (spec.type === 'ImportDefaultSpecifier') return spec.local.name;
        if (spec.type === 'ImportSpecifier') return spec.imported.name;
        return null;
      }).filter(Boolean);
      
      particle.depends_on.push({
        source,
        specifiers: specifiers.length > 0 ? specifiers : null
      });
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
          if (!existing) {
            particle.props.push({ 
              name: p.key.name, 
              default: null, 
              required: true,
              source: node.init.callee.name // Source hook
            });
          }
        });
      } else if (node.id?.type === 'ArrayPattern') {
        // Handle useState and similar hooks that return arrays
        node.id.elements.forEach((element, index) => {
          if (element?.name) {
            const hookName = node.init.callee.name;
            const existing = particle.props.find(prop => prop.name === element.name);
            if (!existing) {
              particle.props.push({ 
                name: element.name, 
                default: null, 
                required: true,
                source: hookName,
                type: index === 1 ? 'setter' : 'state'
              });
            }
          }
        });
      }
    }

    // Route detection - look for route definitions and navigation calls
    if (node.type === 'CallExpression') {
      const callee = node.callee.name || (node.callee.property && `${node.callee.object?.name}.${node.callee.property.name}`);
      if (callee) {
        // Navigation calls
        if (callee === 'router.push' || callee === 'router.replace' || 
            callee === 'navigate' || callee === 'navigateToTab') {
          const arg = node.arguments[0];
          let route = null;
          
          if (arg?.type === 'StringLiteral') {
            route = arg.value;
          } else if (arg?.type === 'TemplateLiteral' && arg.quasis.length > 0) {
            route = arg.quasis[0].value.raw;
          }
          
          if (route) {
            particle.calls.push({
              name: callee,
              args: [route],
              line: node.loc.start.line
            });
            
            // Add to routes if not already there
            if (!particle.routes.find(r => r.path === route)) {
              particle.routes.push({
                path: route,
                type: 'navigation',
                line: node.loc.start.line
              });
            }
          }
        } else if (['withSpring', 'withTiming', 'withSequence', 'withDelay'].includes(callee)) {
          // Animation calls
          particle.calls.push({
            name: callee,
            type: 'animation',
            line: node.loc.start.line
          });
        }
      }
    }
    
    // Route definitions
    if (node.type === 'ObjectExpression' && 
        node.properties?.some(p => p.key?.name === 'path' || p.key?.name === 'element')) {
      const pathProp = node.properties.find(p => p.key?.name === 'path');
      const elementProp = node.properties.find(p => p.key?.name === 'element');
      const componentProp = node.properties.find(p => p.key?.name === 'component');
      
      if (pathProp?.value?.type === 'StringLiteral') {
        const path = pathProp.value.value;
        let component = null;
        
        if (elementProp?.value?.type === 'JSXElement') {
          component = elementProp.value.openingElement.name.name;
        } else if (componentProp?.value?.type === 'Identifier') {
          component = componentProp.value.name;
        }
        
        if (!particle.routes.find(r => r.path === path)) {
          particle.routes.push({
            path,
            component,
            type: 'definition',
            line: node.loc.start.line
          });
        }
      }
    }

    // JSX Elements with enhanced props tracking
    if (node.type === 'JSXElement') {
      const tag = node.openingElement?.name?.name;
      if (tag) {
        // Collect all attributes
        const attrs = {};
        node.openingElement.attributes?.forEach(attr => {
          if (attr.type === 'JSXAttribute') {
            const name = attr.name.name;
            let value = null;
            
            if (attr.value?.type === 'StringLiteral') {
              value = attr.value.value;
            } else if (attr.value?.type === 'JSXExpressionContainer') {
              if (attr.value.expression?.type === 'Identifier') {
                value = attr.value.expression.name;
              } else if (attr.value.expression?.type === 'ArrowFunctionExpression') {
                value = 'function';
              }
            }
            
            if (name.startsWith('on')) {
              // Event handlers
              attrs.events = attrs.events || [];
              attrs.events.push(name);
            } else {
              // Regular props
              attrs.props = attrs.props || [];
              attrs.props.push({ name, value });
            }
          }
        });
        
        particle.jsx.push({
          tag,
          ...attrs,
          line: node.loc.start.line
        });
      }
    }

    // Logic (conditions + detailed actions)
    if (node.type === 'IfStatement') {
      const test = node.test;
      let condition = '';
      
      if (test?.type === 'Identifier') {
        condition = test.name;
      } else if (test?.type === 'BinaryExpression') {
        const left = test.left?.property ? 
          `${test.left.object?.name}.${test.left.property.name}` : 
          (test.left?.name || test.left?.value);
          
        const right = test.right?.property ? 
          `${test.right.object?.name}.${test.right.property.name}` : 
          (test.right?.name || test.right?.value);
          
        condition = `${left || 'unknown'} ${test.operator} ${right || 'unknown'}`;
      } else if (test?.type === 'LogicalExpression') {
        // Handle logical expressions like && and ||
        const left = test.left?.name || 'condition';
        const right = test.right?.name || 'condition';
        condition = `${left} ${test.operator} ${right}`;
      }
      
      if (condition && !condition.includes('unknown')) {
        let action = 'handles condition';
        if (node.consequent.type === 'BlockStatement') {
          node.consequent.body.forEach(stmt => {
            if (stmt.type === 'ReturnStatement' && stmt.argument?.type === 'JSXElement') {
              action = `renders ${stmt.argument.openingElement.name.name}`;
            } else if (stmt.type === 'ExpressionStatement' && 
                      (stmt.expression?.callee?.name === 'router.push' || 
                       stmt.expression?.callee?.name === 'navigate')) {
              action = `navigates to ${stmt.expression.arguments[0]?.value || 'route'}`;
            } else if (stmt.type === 'ExpressionStatement' && 
                       stmt.expression?.type === 'CallExpression') {
              const callee = stmt.expression.callee?.name || 
                           (stmt.expression.callee?.property?.name && 
                            `${stmt.expression.callee.object?.name}.${stmt.expression.callee.property.name}`);
              if (callee) {
                action = `calls ${callee}`;
              }
            }
          });
        }
        
        particle.logic.push({
          condition,
          action,
          line: node.loc.start.line
        });
      }
    }

    // State Machines (e.g., EVENT_STATES, state objects, or reducers)
    if (node.type === 'VariableDeclarator' && 
        (node.id.name?.endsWith('_STATES') || node.id.name?.endsWith('States'))) {
      
      let states = [];
      
      if (node.init?.type === 'ObjectExpression') {
        states = node.init.properties?.map(prop => ({
          name: prop.key.name || prop.key.value,
          value: prop.value?.value
        })) || [];
      }
      
      if (states.length > 0) {
        particle.state_machine = {
          name: node.id.name,
          states,
          line: node.loc.start.line
        };
      }
    } else if (node.type === 'CallExpression' && 
              (node.callee?.name === 'useReducer' || node.callee?.name === 'createReducer')) {
      // Look for reducer functions which often contain state machines
      const reducerArg = node.arguments[0];
      if (reducerArg?.type === 'Identifier') {
        particle.state_machine = {
          name: `${reducerArg.name} (reducer)`,
          type: 'reducer',
          line: node.loc.start.line
        };
      }
    }

    // Recurse
    for (const key in node) if (node[key] && typeof node[key] === 'object') enhanceWalk(node[key]);
  }

  walk(ast);
  // Always run enhanceWalk now
  enhanceWalk(ast);

  // Merge with existing Particle
  const existingMatch = code.match(/export const Particle = \{[\s\S]*?\};/);
  if (existingMatch) {
    try {
      const cleanedCode = existingMatch[0].replace('export const Particle =', '').trim().replace(/;$/, '');
      const existing = eval(`(${cleanedCode})`);
      
      // Smart merge of existing data
      particle.purpose = existing.purpose || particle.purpose;
      
      // For arrays, merge with deduplication
      ['props', 'hooks', 'calls', 'logic', 'depends_on', 'jsx', 'routes', 'comments'].forEach(field => {
        if (existing[field]) {
          // For simple arrays, deduplicate by stringified value
          if (typeof existing[field][0] !== 'object') {
            particle[field] = [...new Set([...(existing[field] || []), ...particle[field]])];
          } else {
            // For object arrays, try to merge intelligently
            const merged = [...existing[field]];
            particle[field].forEach(item => {
              // Skip if exact match exists
              if (!merged.some(m => JSON.stringify(m) === JSON.stringify(item))) {
                merged.push(item);
              }
            });
            particle[field] = merged;
          }
        }
      });
      
      // For single objects like state_machine, keep existing if it has more info
      if (existing.state_machine && (!particle.state_machine || 
          existing.state_machine.states?.length > (particle.state_machine.states?.length || 0))) {
        particle.state_machine = existing.state_machine;
      }
    } catch (e) {
      console.error(`Failed to parse existing Particle in ${filePath}: ${e.message}`);
    }
  }

  // Filter empty fields
  Object.keys(particle).forEach(key => {
    if (Array.isArray(particle[key]) && particle[key].length === 0) delete particle[key];
    if (key === 'state_machine' && (!particle[key] || 
        (particle[key].states && particle[key].states.length === 0))) delete particle[key];
  });

  console.log(JSON.stringify(particle, null, 2));
} catch (error) {
  console.error(`Error parsing ${filePath}: ${error.message}`);
  process.exit(1);
}