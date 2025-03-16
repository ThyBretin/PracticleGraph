const { parse } = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const fs = require('fs');
const path = require('path');

function extractMetadata(filePath, rich = false) {
  if (!filePath.endsWith('.js') && !filePath.endsWith('.jsx')) {
    process.stderr.write(`Skipping non-JS file: ${filePath}\n`);
    return null;
  }

  let code;
  try {
    code = fs.readFileSync(filePath, 'utf-8');
  } catch (e) {
    process.stderr.write(`Failed to read ${filePath}: ${e.message}\n`);
    return null;
  }

  let ast;
  try {
    ast = parse(code, {
      sourceType: 'module',
      plugins: ['jsx', 'flow'],
      errorRecovery: true,
    });
  } catch (e) {
    process.stderr.write(`Babel parse failed for ${filePath}: ${e.message}\n`);
    return null;
  }

  const fileExt = path.extname(filePath);
  const particle = {
    path: path.relative(process.cwd(), filePath),
    type: fileExt === '.jsx' ? 'component' : 'file',
    purpose: `Handles ${path.basename(filePath, fileExt).toLowerCase()} functionality`,
    hooks: {},
    calls: {},
    logic: [],
    depends_on: {},
    core_rules: [],
    variables: {},
    functions: {},
    references: { hooks: {}, calls: {}, routes: {} },
    business_rules: [],
    flows: [],
    endpoints: [],
    env: [],
  };

  traverse(ast, {
    VariableDeclarator({ node }) {
      if (node.id.name === 'Particle') return;
      const name = node.id.name || (node.id.type === 'ObjectPattern' ? 'destructured' : 'unknown');
      const line = node.loc?.start?.line || 0;
      particle.variables[name] = particle.variables[name] || [];
      particle.variables[name].push(line);

      if (node.init && node.init.type === 'CallExpression') {
        const hookName = node.init.callee.name;
        if (hookName && /^use[A-Z]/.test(hookName)) {
          particle.hooks[hookName] = particle.hooks[hookName] || [];
          particle.hooks[hookName].push(line);
          particle.references.hooks[hookName] = particle.references.hooks[hookName] || [];
          particle.references.hooks[hookName].push(line);
          if (node.id.type === 'ObjectPattern') {
            node.id.properties.forEach(prop => {
              const propName = prop.value.name;
              particle.calls[propName] = particle.calls[propName] || [];
              particle.calls[propName].push(line);
              particle.references.calls[propName] = particle.references.calls[propName] || [];
              particle.references.calls[propName].push(line);
            });
          }
        }
      }
    },

    FunctionDeclaration({ node }) {
      const name = node.id?.name;
      if (name) {
        const line = node.loc?.start?.line || 0;
        particle.functions[name] = particle.functions[name] || [];
        particle.functions[name].push(line);
      }
    },

    ImportDeclaration({ node }) {
      const source = node.source.value;
      const specifiers = node.specifiers.map(spec => spec.local.name);
      particle.depends_on[source] = particle.depends_on[source] || [];
      particle.depends_on[source].push(...specifiers);
      if (source.includes('dotenv')) particle.env.push('Loads environment variables');
      if (source.includes('supabase')) particle.env.push('SUPABASE_URL: DB access');
      if (source.includes('stripe')) particle.env.push('STRIPE_KEY: Payments');
    },

    CallExpression({ node }) {
      const callee = node.callee;
      if (callee.name && /^use[A-Z]/.test(callee.name)) {
        const line = node.loc?.start?.line || 0;
        particle.hooks[callee.name] = particle.hooks[callee.name] || [];
        particle.hooks[callee.name].push(line);
        particle.references.hooks[callee.name] = particle.references.hooks[callee.name] || [];
        particle.references.hooks[callee.name].push(line);
      }

      let callName;
      if (callee.type === 'Identifier') {
        callName = callee.name;
      } else if (callee.type === 'MemberExpression') {
        callName = `${callee.object.name}.${callee.property.name}`;
      }
      if (callName) {
        const line = node.loc?.start?.line || 0;
        particle.calls[callName] = particle.calls[callName] || [];
        particle.calls[callName].push(line);
        particle.references.calls[callName] = particle.references.calls[callName] || [];
        particle.references.calls[callName].push(line);
        if (callee.object?.name === 'supabase') {
          const method = callee.property.name;
          const table = node.arguments[0]?.value;
          if (method && table) particle.endpoints.push(`${method === 'from' ? 'GET' : 'POST'} /${table}`);
        }
      }

      if (node.callee.property?.name === 'replace') {
        const route = node.arguments[0]?.value;
        if (route) {
          const line = node.loc?.start?.line || 0;
          particle.routes = particle.routes || [];
          particle.routes.push(route);
          particle.references.routes[route] = particle.references.routes[route] || [];
          particle.references.routes[route].push(line);
        }
      }
    },

    IfStatement({ node }) {
      if (node.test) {
        let condition = '';
        if (node.test.type === 'Identifier') condition = node.test.name;
        else if (node.test.type === 'UnaryExpression' && node.test.operator === '!') {
          condition = `!${node.test.argument?.name || 'check'}`;
        } else if (node.test.type === 'BinaryExpression') {
          condition = `${node.test.left?.name || ''} ${node.test.operator} ${node.test.right?.name || ''}`;
        } else if (node.test.type === 'LogicalExpression') {
          condition = `${node.test.left?.name || ''} ${node.test.operator} ${node.test.right?.name || ''}`;
        }

        if (condition) {
          let action = 'handles condition';
          if (node.consequent.type === 'BlockStatement') {
            node.consequent.body.forEach(stmt => {
              if (stmt.type === 'ExpressionStatement' && stmt.expression?.type === 'CallExpression') {
                const callee = stmt.expression.callee?.name || 
                  (stmt.expression.callee?.property?.name && `${stmt.expression.callee.object?.name}.${stmt.expression.callee.property.name}`);
                if (callee === 'console.error') action = 'logs error';
                else if (callee?.includes('router')) action = `redirects to ${stmt.expression.arguments[0]?.value || 'route'}`;
                else if (callee) action = `calls ${callee}`;
              } else if (stmt.type === 'VariableDeclaration') action = 'sets variable';
            });
          }

          const logicEntry = { condition, action, line: node.loc?.start?.line || 0 };
          particle.logic.push(logicEntry);
          if (rich && isCoreRule(logicEntry, particle)) {
            particle.core_rules.push(logicEntry);
          }
        }
      }
    },
  });

  if (rich) {
    if (particle.routes?.includes('/(auth)/login')) particle.flows.push('Onboarding: /(auth)/login → discovery');
    if (particle.logic.some(l => l.action.includes('redirect'))) particle.flows.push('Booking: discovery → event → ticket');
    particle.core_rules.forEach(rule => {
      if (rule.condition.includes('capacity')) {
        particle.business_rules.push('Capacity drives stage: Balanced capacity triggers shift');
      } else if (rule.action.includes('redirect')) {
        particle.business_rules.push(`Navigation rule: ${rule.condition} → ${rule.action}`);
      }
    });
    if (particle.depends_on['stripe']) {
      particle.business_rules.push('Revenue split: Organizers and venues divide sales');
    }
  }

  return {
    id: path.basename(filePath),
    type: particle.type,
    label: path.basename(filePath),
    attributes: {
      path: particle.path,
      purpose: particle.purpose,
      hooks: Object.entries(particle.hooks).map(([name, lines]) => ({ name, lines: [...new Set(lines)] })),
      calls: Object.entries(particle.calls).map(([name, lines]) => ({ name, lines: [...new Set(lines)] })),
      variables: Object.entries(particle.variables).map(([name, lines]) => ({ name, lines: [...new Set(lines)] })),
      functions: Object.entries(particle.functions).map(([name, lines]) => ({ name, lines: [...new Set(lines)] })),
      core_rules: particle.core_rules,
      depends_on: Object.entries(particle.depends_on).map(([source, specifiers]) => `${source} (${[...new Set(specifiers)].join(', ')})`),
      ...(rich && {
        business_rules: particle.business_rules,
        flows: particle.flows,
        endpoints: particle.endpoints,
        env: particle.env,
      }),
    },
  };
}

function isCoreRule(logicEntry, particle) {
  const { condition, action } = logicEntry;
  let score = 0;
  if (action.includes('redirect') || action.includes('calls') || action.includes('sets')) score += 3;
  if (condition.includes('&&') || condition.includes('||') || condition.includes('===')) score += 2;
  const deps = Object.keys(particle.depends_on).join(' ').toLowerCase();
  if (deps && (condition.toLowerCase().includes(deps) || action.toLowerCase().includes(deps))) score += 2;
  return score >= 5;
}

if (require.main === module) {
  const pathArg = process.argv[2];
  if (!pathArg) {
    process.stderr.write('Please provide a file path\n');
    process.exit(1);
  }
  try {
    const stat = fs.statSync(pathArg);
    if (stat.isDirectory()) {
      process.stderr.write('Directory processing not supported in this mode\n');
      process.exit(1);
    }
    const particle = extractMetadata(pathArg, true);
    if (particle) {
      console.log(JSON.stringify(particle, null, 2));
    } else {
      process.stderr.write(`No metadata extracted for ${pathArg}\n`);
      process.exit(1);
    }
  } catch (e) {
    process.stderr.write(`Failed to process ${pathArg}: ${e.message}\n`);
    process.exit(1);
  }
}

module.exports = { extractMetadata };