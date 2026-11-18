// SPDX-License-Identifier: AGPL-3.0-or-later
/* The relay on this computer alone, for the suite's area 342 and for trying it out: Miniflare (the
   engine `wrangler dev` runs) with the relay's Durable Objects, an R2 bucket in a folder, the invite
   limit, a made-up operator key and the old relay's made-up operator code, on 127.0.0.1 and nowhere else. It
   asks nothing of Cloudflare: `cf: false` keeps Miniflare from fetching its request.cf data.

     node relay/test/serve.mjs --port 8860 --operator-key test-key-0123456789 [--codes test-code-0123456789]
          [--persist DIR] [--miniflare PATH] [--script relay/test/worker_v1.js] [--test-limits '{"waiting": 300000}']

   --script runs another worker, the old one area 342 starts on the same storage before or after the new, and
   --codes are the codes that old one asks to start a project. --test-limits lays smaller limits over the worker's
   own, so a check reaches them with a few hundred kilobytes, or a project's alarm comes in seconds.

   Miniflare comes from relay/node_modules when `npm install` has run there, or from PATH, the
   folder of Wrangler's own copy (`<wrangler>/node_modules/miniflare`). It prints "ready <url>" once
   it answers, and stops on SIGTERM or when its input closes. */

import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
import { readFileSync } from 'node:fs';

const args = Object.fromEntries(process.argv.slice(2).reduce((out, a, i, all) => {
  if (a.startsWith('--')) out.push([a.slice(2), all[i + 1]]);
  return out;
}, []));
const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');

let mod;
if (args.miniflare) mod = await import(pathToFileURL(path.join(args.miniflare, 'dist', 'src', 'index.js')).href);
else mod = await import('miniflare');
const { Miniflare } = mod;

const persist = args.persist || false;
const limit = Number(args['invite-limit'] || 30);
// new projects from one address a minute, the same as the invites' unless given
const projectLimit = Number(args['project-limit'] || limit);
const scriptPath = args.script ? path.resolve(args.script) : path.join(root, 'src', 'worker.js');
const scriptText = readFileSync(scriptPath, 'utf8');
const hasCounter = /export class Counter\b/.test(scriptText);
const vars = { JURISDICTION: '', OPERATOR_KEY: args['operator-key'] || '', ...(args['test-limits'] ? { TEST_LIMITS: args['test-limits'] } : {}) };
const operatorCodes = args.codes || '';

// Two Miniflares, two shapes of options. The one in Wrangler 4.97 takes the worker's options flat
// (modules, durableObjects, r2Buckets, bindings). The one in Wrangler 4.158 takes `workers: [...]`,
// each with a `config` of typed `env` bindings, `exports` and a `manifest` holding the module's text,
// and its storage under one `resourcePersistencePath`. It is told apart by exporting
// MiniflareWorkerConfigSchema.
function optionsFor(m) {
  if (m.MiniflareWorkerConfigSchema) {
    return {
      host: '127.0.0.1',
      port: Number(args.port),
      cf: false,
      logRequests: false,
      enableDevRegistry: false,
      ...(persist ? { resourcePersistencePath: path.resolve(persist) } : {}),
      workers: [{
        config: {
          name: 'relay',
          compatibilityDate: '2026-06-01',
          manifest: {
            mainModule: 'src/worker.js',
            modulesRoot: root,
            modules: { 'src/worker.js': { type: 'esm', contents: scriptText } },
          },
          exports: {
            Project: { type: 'durable-object', storage: 'sqlite' },
            Invite: { type: 'durable-object', storage: 'sqlite' },
            Operator: { type: 'durable-object', storage: 'sqlite' },
            ...(hasCounter ? { Counter: { type: 'durable-object', storage: 'sqlite' } } : {}),
          },
          env: {
            PROJECTS: { type: 'durable-object', worker: 'relay', exportName: 'Project' },
            INVITES: { type: 'durable-object', worker: 'relay', exportName: 'Invite' },
            OPERATORS: { type: 'durable-object', worker: 'relay', exportName: 'Operator' },
            ...(hasCounter ? { COUNTER: { type: 'durable-object', worker: 'relay', exportName: 'Counter' } } : {}),
            BLOBS: { type: 'r2', name: 'BLOBS' },
            INVITE_LIMIT: { type: 'rate-limit', namespace: 'INVITE_LIMIT', simple: { limit, period: 60 } },
            PROJECT_LIMIT: { type: 'rate-limit', namespace: 'PROJECT_LIMIT', simple: { limit: projectLimit, period: 60 } },
            OPERATOR_CODES: { type: 'text', value: operatorCodes },
            ...Object.fromEntries(Object.entries(vars).map(([k, v]) => [k, { type: 'text', value: v }])),
          },
        },
      }],
    };
  }
  return {
    modules: true,
    scriptPath,
    // the modules' root named, so a run from any folder finds them
    modulesRoot: root,
    compatibilityDate: '2026-06-01',
    host: '127.0.0.1',
    port: Number(args.port),
    cf: false,
    durableObjects: {
      PROJECTS: { className: 'Project', useSQLite: true },
      INVITES: { className: 'Invite', useSQLite: true },
      OPERATORS: { className: 'Operator', useSQLite: true },
      ...(hasCounter ? { COUNTER: { className: 'Counter', useSQLite: true } } : {}),
    },
    r2Buckets: ['BLOBS'],
    ratelimits: { INVITE_LIMIT: { simple: { limit, period: 60 } }, PROJECT_LIMIT: { simple: { limit: projectLimit, period: 60 } } },
    bindings: { OPERATOR_CODES: operatorCodes, ...vars },
    durableObjectsPersist: persist && path.join(persist, 'do'),
    r2Persist: persist && path.join(persist, 'r2'),
  };
}
const mf = new Miniflare(optionsFor(mod));
const url = await mf.ready;
process.stdout.write(`ready ${url.href}\n`);

const stop = async () => {
  await mf.dispose();
  process.exit(0);
};
process.on('SIGTERM', stop);
process.on('SIGINT', stop);
process.stdin.on('end', stop);
process.stdin.resume();
