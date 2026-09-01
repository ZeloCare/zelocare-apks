# zelocare-apks

Repositório central para APKs do ZeloCare — builds manuais via `workflow_dispatch` no runner `zelocare-static`.

## Como usar

1. Vai a **Actions → Build APKs → Run workflow**
2. Escolhe `app`: `all` (as duas), `zelocare-mobile` ou `zelocare-volunteer`
3. O job faz:
   - `npm ci --legacy-peer-deps`
   - `npx expo prebuild --platform android`
   - `./gradlew assembleRelease`
   - Upload do APK como artifact (`retention 30d`)

APKs ficam em **Actions → Artifacts** para download. Tag opcional: descomenta o step `softprops/action-gh-release` no workflow para publicar em Releases.

## Requisitos

- Runner `zelocare-static` com `setup-java` 17 + `setup-android` (SDK descarregado em runtime)
- Secret `GH_PAT` com `repo` scope para checkout das apps privadas (adicionar em Settings → Secrets → Actions)
