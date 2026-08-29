# Monorepo Shape and Config

Verified 29 August 2026. This is the fastest-ageing file in the plugin — check every version against the live registry with `npx expo install --check` and the SDK changelog before installing: https://expo.dev/changelog

## Directory tree

```
repo/
  package.json                  # private: true, packageManager: "pnpm@11.24.0"
  pnpm-workspace.yaml
  turbo.json
  tsconfig.base.json
  .npmrc
  .nvmrc                        # 22.13.0 — SDK 57 Node minimum
  apps/
    mobile/
      app/                      # expo-router routes
        _layout.tsx
        (tabs)/_layout.tsx
        (auth)/sign-in.tsx
        [...not-found].tsx
      app.json                  # static defaults
      app.config.ts             # dynamic: variants, env
      eas.json
      metro.config.js
      package.json
      .maestro/
    web/
      app/                      # Next.js App Router
      next.config.ts
      package.json
  packages/
    ui/                         # cross-platform components (.tsx + .web.tsx)
    config/                     # tsconfig/eslint/tailwind presets + zod env schema
    api/                        # Hono app + tRPC router; exports AppRouter type only
    db/                         # drizzle schema + migrations — SERVER ONLY
    i18n/
  .eas/workflows/               # EAS Workflows YAML
  .github/workflows/            # lint / typecheck / unit tests only
  docs/app/stack.md
```

Rule: `packages/db` must never be imported from `apps/mobile` or from a client component in `apps/web`. Enforce it with an ESLint `no-restricted-imports` rule in the mobile and web configs, not with discipline.

## Package manager

**pnpm 11.24.0 is the default.** Expo has first-class monorepo support for pnpm, npm, Bun, and Yarn (v1 and Berry) and auto-detects the workspace ([guides/monorepos](https://docs.expo.dev/guides/monorepos/)). pnpm gives the best determinism-to-pain ratio. Bun 1.4 workspaces work. npm workspaces work but hoist unpredictably. Yarn Berry PnP is still a losing fight against native builds.

```yaml
# pnpm-workspace.yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

Workspace dependencies use the protocol so a same-named public package can never resolve instead:

```json
{ "dependencies": { "@repo/ui": "workspace:*", "@repo/api": "workspace:*" } }
```

### Isolated vs hoisted installs

pnpm and Bun default to **isolated** installs: no hoisting, a central store, symlinks, and packages can only reach their declared dependencies. Expo supports isolated installs **from SDK 54**. But not every React Native library declares its dependencies correctly, and those libraries fail at native build time, not install time.

**Switch to hoisted the moment you hit a native build or resolution error you cannot attribute to anything else.** This is a normal, supported outcome — not a defeat.

```yaml
# pnpm-workspace.yaml
nodeLinker: hoisted
```

For Bun, use the non-isolated linker. After switching, delete `node_modules` at every level, reinstall, and run `npx expo start --clear`.

The cost of hoisting: you can accidentally import packages you never declared, and that breaks later during an upgrade. Mitigate with `pnpm dedupe --check` in CI.

## Source-only TypeScript packages

Ship shared packages as **raw TypeScript with no build step**. Metro and Next both transpile them. This eliminates the entire "stale `dist/`" class of monorepo bug, where a package's `main` points at output from two commits ago.

```json
{
  "name": "@repo/ui",
  "version": "0.0.0",
  "private": true,
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "exports": {
    ".": "./src/index.ts",
    "./*": "./src/*.ts"
  },
  "sideEffects": false,
  "dependencies": {},
  "peerDependencies": {
    "react": "*",
    "react-native": "*"
  },
  "devDependencies": {
    "@repo/config": "workspace:*",
    "typescript": "~6.0.3"
  },
  "scripts": {
    "typecheck": "tsc --noEmit",
    "lint": "eslint ."
  }
}
```

Keep `react` and `react-native` in `peerDependencies` only. Listing them as `dependencies` is the single most common way to get two copies in the tree.

Platform variants inside a package work by extension: `Button.tsx` (native), `Button.web.tsx` (web). Metro resolves `.native.tsx`/`.ios.tsx`/`.android.tsx`/`.tsx`; Next needs `resolveExtensions` configured (below) to prefer `.web.tsx`.

## Do not hand-write Metro monorepo config

From **SDK 52**, `expo/metro-config` detects the workspace and configures Metro. Manual config now actively fights it.

Delete these keys if you find them in `metro.config.js`:

- `watchFolders`
- `resolver.nodeModulesPath` / `resolver.nodeModulesPaths`
- `resolver.extraNodeModules`
- `resolver.disableHierarchicalLookup`

Then reset the cache once:

```sh
npx expo start --clear
```

If the app still works, it is a plain Node monorepo and needs no special config going forward ([guides/monorepos](https://docs.expo.dev/guides/monorepos/)).

The correct `apps/mobile/metro.config.js` is minimal:

```js
const { getDefaultConfig } = require('expo/metro-config');

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(__dirname);

// Only your own additions below — e.g. NativeWind, svg transformer.
module.exports = config;
```

### Autolinking module resolution

`experiments.autolinkingModuleResolution: true` in app config forces Metro's JS resolution to match the native modules autolinking actually links, so the JS half and native half of a module can never disagree. Available from SDK 54; **enabled automatically for apps inside a monorepo from SDK 55**. Set it explicitly if you are on SDK 54.

```json
{ "expo": { "experiments": { "autolinkingModuleResolution": true } } }
```

## The single-copy rule

Non-negotiable, per [guides/monorepos](https://docs.expo.dev/guides/monorepos/):

- **Duplicate `react-native` versions in one monorepo are not supported.**
- **Duplicate `react` versions in one app cause runtime errors.**
- Duplicate Turbo modules / Expo modules cause runtime or build errors.
- Any native module duplicated is fatal: only one version of a native module can be compiled into a build.
- Packages creating a React context (theme providers, query clients) break when duplicated even though they are not native.

Diagnose:

```sh
pnpm why --depth=10 react-native
pnpm why --depth=10 react
npm why react-native        # npm
yarn why react-native       # yarn
bun pm why react-native     # bun
```

Look for two version strings in the output. Fix by aligning declared versions first; only if that is impossible, force a resolution at the root:

```json
{
  "name": "repo",
  "private": true,
  "resolutions": {
    "react": "19.2.3",
    "react-dom": "19.2.3",
    "react-native": "0.86.3"
  }
}
```

pnpm, Yarn, and Bun read `resolutions`; **npm uses `overrides`** with the same shape. pnpm also accepts `pnpm.overrides`.

## Turborepo

Turborepo `2.10.12`, not Nx. Nx 23 only earns its configuration cost past roughly 15 packages; below that it is overhead.

```json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["tsconfig.base.json", ".env.example"],
  "tasks": {
    "dev": { "cache": false, "persistent": true },
    "build": { "dependsOn": ["^build"], "outputs": [".next/**", "!.next/cache/**", "dist/**"] },
    "typecheck": { "dependsOn": ["^typecheck"], "outputs": [] },
    "lint": { "outputs": [] },
    "test": { "dependsOn": ["^build"], "outputs": ["coverage/**"] }
  }
}
```

Source-only packages have no `build` task, so `^build` resolves to a no-op for them — that is fine and intended.

## TypeScript: path aliases, not project references

Project references force every shared package to emit `.d.ts` before consumers typecheck, which reintroduces the build step that source-only packages exist to avoid. Use path aliases.

```json
// tsconfig.base.json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "verbatimModuleSyntax": true,
    "moduleResolution": "bundler",
    "module": "esnext",
    "target": "esnext",
    "jsx": "react-jsx",
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "baseUrl": ".",
    "paths": {
      "@repo/ui": ["packages/ui/src/index.ts"],
      "@repo/ui/*": ["packages/ui/src/*"],
      "@repo/api": ["packages/api/src/index.ts"],
      "@repo/config/*": ["packages/config/*"],
      "@repo/i18n": ["packages/i18n/src/index.ts"]
    }
  }
}
```

```json
// apps/mobile/tsconfig.json
{
  "extends": ["expo/tsconfig.base", "../../tsconfig.base.json"],
  "compilerOptions": {
    "baseUrl": "../..",
    "paths": {
      "@/*": ["apps/mobile/*"],
      "@repo/ui": ["packages/ui/src/index.ts"],
      "@repo/api": ["packages/api/src/index.ts"]
    }
  },
  "include": ["**/*.ts", "**/*.tsx", ".expo/types/**/*.ts", "expo-env.d.ts"]
}
```

Metro honours `tsconfig` paths through `expo/metro-config` — no extra resolver config needed. In CI, typed routes need the generated types to exist without a dev server running:

```sh
npx expo customize tsconfig.json && tsc --noEmit
```

Add `expo-env.d.ts`, `.expo/`, and `dist/` to `.gitignore`.

## Next.js interop

**`@expo/next-adapter` is abandoned** — last publish `6.0.0` on 8 Jan 2024, and the Expo guide that recommends it ([guides/using-nextjs](https://docs.expo.dev/guides/using-nextjs/)) still references the `pages/` directory and `swcMinify`. Expo also states plainly that "Using Next.js is not an official part of Expo's universal app development workflow." Do not install the adapter. Configure Next.js directly.

```ts
// apps/web/next.config.ts
import type { NextConfig } from 'next';

const rnPackages = [
  'react-native',          // required even though unused directly:
                           // react-native-web is aliased *to* react-native
  'react-native-web',
  'expo',
  'expo-modules-core',
  'expo-constants',
  'expo-linking',
  'nativewind',
  'react-native-css',
  'react-native-safe-area-context',
  '@repo/ui',
  '@repo/api',
  '@repo/i18n',
];

const config: NextConfig = {
  reactStrictMode: true,
  transpilePackages: rnPackages,

  turbopack: {
    resolveAlias: {
      'react-native': 'react-native-web',
    },
    resolveExtensions: [
      '.web.tsx', '.web.ts', '.web.jsx', '.web.js',
      '.tsx', '.ts', '.jsx', '.js',
      '.mjs', '.json',
    ],
  },

  webpack: (cfg) => {
    cfg.resolve.alias = {
      ...cfg.resolve.alias,
      'react-native$': 'react-native-web',
    };
    cfg.resolve.extensions = [
      '.web.tsx', '.web.ts', '.web.jsx', '.web.js',
      ...cfg.resolve.extensions,
    ];
    return cfg;
  },
};

export default config;
```

`react-native-web` assumes a CSS reset. In the App Router, put the reset in `apps/web/app/globals.css` (the old `pages/_document.tsx` `AppRegistry.getApplication` dance is a `pages/`-only pattern):

```css
html, body, #__next { -webkit-overflow-scrolling: touch; }
html { scroll-behavior: smooth; -webkit-text-size-adjust: 100%; }
body {
  overflow-y: auto; overscroll-behavior-y: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
}
```

Troubleshooting: `Cannot use import statement outside a module` at Next build time means an untranspiled RN-ecosystem package. Find it in the stack trace, add it to `transpilePackages`, restart. This will happen repeatedly as you add libraries — treat the array as a growing list, not a fixed one.

Also note `react-native-web@0.21.2` last published Oct 2025. It is stable but slow-moving, and it lags RN's newer APIs.

## Alternative: drop Next.js, use Expo Router for web

Expo Router 57 does static site generation, **streaming SSR** (`generateMetadata`, `SuspenseFallback` exports from `_layout` — added in SDK 56), server routes (`+api.ts`), and server middleware (`+middleware.ts`). `apps/web` becomes `npx expo export -p web`, deployed with `eas deploy` or any static/Node host.

**Choose this when:**
- The web surface is the same product as the app (a dashboard, an account area, a logged-in experience).
- You want one bundler, one router, one styling pipeline, and one set of components with no `transpilePackages` maintenance and no `react-native-web` alias drift.
- The team is small and the interop tax is a real fraction of their time.

**Keep Next.js when:**
- You need RSC-heavy marketing and SEO pages, ISR, or a CMS integration that assumes Next.
- Web checkout / billing flows want Next's server actions and middleware ecosystem.
- A Next app already exists and rewriting it is not on the table.

The middle path that usually wins: **Next.js for the marketing site and checkout only** (its own routes, its own components, minimal RN sharing), and Expo Router for everything logged-in on both platforms. That keeps `transpilePackages` short because the shared surface between Next and RN is deliberately small.
