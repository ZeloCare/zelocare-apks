# ZeloCare APKs

Repositório público de distribuição interna dos APKs Android da ZeloCare:

- `zelocare-mobile` — `com.zelocare.app`
- `zelocare-volunteer` — `com.zelocare.volunteerv2`

Os binários são publicados em [GitHub Releases](../../releases); não são adicionados ao histórico Git.


## Gerar APKs

1. Abre **Actions → Build and publish APKs → Run workflow**.
2. Escolhe `all`, `zelocare-mobile` ou `zelocare-volunteer`.
3. Mantém as refs em `main` ou indica uma branch, tag ou SHA para cada aplicação.
4. Inicia o workflow e aguarda pelos jobs de validação, build e publicação.

Cada execução bem-sucedida cria:

- Uma release histórica imutável, com APK, checksum SHA-256 e metadados do commit compilado.
- A release [`latest`](../../releases/tag/latest), com URLs estáveis:
  - `zelocare-mobile-latest.apk`
  - `zelocare-volunteer-latest.apk`

Quando apenas uma aplicação é compilada, o APK `latest` da outra aplicação é preservado.

## Secrets necessários

| Secret | Finalidade |
| --- | --- |
| `SOURCE_REPOS_TOKEN` | Fine-grained PAT com acesso **Contents: read** a `zelocare-mobile` e `zelocare-volunteer` |
| `MOBILE_ANDROID_KEYSTORE_BASE64` | Keystore JKS da app mobile codificado em base64 |
| `MOBILE_ANDROID_KEY_ALIAS` | Alias da chave mobile |
| `MOBILE_ANDROID_STORE_PASSWORD` | Password do keystore mobile |
| `MOBILE_ANDROID_KEY_PASSWORD` | Password da chave mobile |
| `MOBILE_ANDROID_CERT_SHA256` | Fingerprint SHA-256 do certificado mobile |
| `VOLUNTEER_ANDROID_KEYSTORE_BASE64` | Keystore JKS da app volunteer codificado em base64 |
| `VOLUNTEER_ANDROID_KEY_ALIAS` | Alias da chave volunteer |
| `VOLUNTEER_ANDROID_STORE_PASSWORD` | Password do keystore volunteer |
| `VOLUNTEER_ANDROID_KEY_PASSWORD` | Password da chave volunteer |
| `VOLUNTEER_ANDROID_CERT_SHA256` | Fingerprint SHA-256 do certificado volunteer |

O `GITHUB_TOKEN` nativo publica as releases através da permissão `contents: write`. O token de leitura dos repositórios fonte não é usado para publicar.

## Assinatura e atualizações

Cada aplicação usa uma chave estável e distinta. O workflow valida o fingerprint depois do build e recusa publicar um APK assinado por outra chave. O `versionCode` é crescente (`100000 + github.run_number`), permitindo instalar um build mais recente por cima do anterior.

Para verificar manualmente um download:

```bash
sha256sum -c zelocare-mobile-latest.apk.sha256
apksigner verify --verbose --print-certs zelocare-mobile-latest.apk
```

### Rotação de chaves

Não substituas um keystore isoladamente: Android rejeitará a atualização sobre instalações existentes. Para uma rotação planeada, preserva primeiro uma cópia offline do keystore atual, prepara a estratégia de migração de assinatura e atualiza em conjunto o keystore e o respetivo fingerprint. Os valores das chaves nunca devem ser guardados no Git nem anexados às releases.

## Diagnóstico

- **Ref inválida:** confirma que a branch, tag ou SHA existe no respetivo repositório.
- **Falha no checkout:** confirma o `SOURCE_REPOS_TOKEN` e o seu acesso aos dois repositórios privados.
- **Fingerprint diferente:** não publiques o APK; confirma se o keystore e o fingerprint pertencem à mesma app.
- **Atualização recusada no Android:** confirma package ID, assinatura e se o novo `versionCode` é superior ao instalado.
