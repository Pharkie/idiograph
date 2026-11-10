// SPDX-License-Identifier: AGPL-3.0-or-later
/* The relay on this computer alone, for the suite's area 342 and for trying it out: Miniflare (the
   engine `wrangler dev` runs) with the relay's Durable Objects, an R2 bucket in a folder, the invite
   limit and a made-up operator code, on 127.0.0.1 and nowhere else. It asks nothing of Cloudflare:
   `cf: false` keeps Miniflare from fetching its request.cf data.

     node relay/test/serve.mjs --port 8860 --codes test-code-0123456789 [--persist DIR] [--miniflare PATH]

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
const scriptPath = path.join(root, 'src', 'worker.js');
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
            modules: { 'src/worker.js': { type: 'esm', contents: readFileSync(scriptPath, 'utf8') } },
          },
          exports: {
            Project: { type: 'durable-object', storage: 'sqlite' },
            Invite: { type: 'durable-object', storage: 'sqlite' },
            Operator: { type: 'durable-object', storage: 'sqlite' },
          },
          env: {
            PROJECTS: { type: 'durable-object', worker: 'relay', exportName: 'Project' },
            INVITES: { type: 'durable-object', worker: 'relay', exportName: 'Invite' },
            OPERATORS: { type: 'durable-object', worker: 'relay', exportName: 'Operator' },
            BLOBS: { type: 'r2', name: 'BLOBS' },
            INVITE_LIMIT: { type: 'rate-limit', namespace: 'INVITE_LIMIT', simple: { limit, period: 60 } },
            OPERATOR_CODES: { type: 'text', value: operatorCodes },
            JURISDICTION: { type: 'text', value: '' },
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
    },
    r2Buckets: ['BLOBS'],
    ratelimits: { INVITE_LIMIT: { simple: { limit, period: 60 } } },
    bindings: { OPERATOR_CODES: operatorCodes, JURISDICTION: '' },
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
