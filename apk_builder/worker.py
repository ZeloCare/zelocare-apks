"""Short-lived Kubernetes worker that builds and publishes signed APKs."""
import base64, json, os, shutil, subprocess, time
from pathlib import Path

WORK = Path('/work'); WORK.mkdir(exist_ok=True)
def run(*args, cwd=None, env=None): subprocess.run(args, cwd=cwd, env=env, check=True)
def value(prefix, key): return os.environ[f'{prefix}_{key}']

def build(app, ref):
    prefix = 'MOBILE_ANDROID' if app == 'zelocare-mobile' else 'VOLUNTEER_ANDROID'
    package = 'com.zelocare.app' if app == 'zelocare-mobile' else 'com.zelocare.volunteerv2'
    source = WORK / app
    run('git', 'clone', f"https://x-access-token:{os.environ['SOURCE_REPOS_TOKEN']}@github.com/ZeloCare/{app}.git", str(source))
    run('git', 'checkout', '--detach', ref, cwd=source)
    run('npm', 'ci', '--legacy-peer-deps', cwd=source); run('npx', 'tsc', '--noEmit', cwd=source)
    if app == 'zelocare-mobile': run('npx', 'jest', '--passWithNoTests', '--runInBand', cwd=source)
    cfg = json.loads((source/'app.json').read_text()); cfg['expo'].setdefault('android', {})['versionCode'] = int(os.environ['VERSION_CODE'])
    (source/'app.json').write_text(json.dumps(cfg, indent=2)+'\n'); run('npx', 'expo', 'prebuild', '--platform', 'android', '--non-interactive', cwd=source)
    key = WORK/f'{app}.jks'; key.write_bytes(base64.b64decode(value(prefix, 'KEYSTORE_BASE64'))); os.chmod(key, 0o600)
    try:
        run('./gradlew', '--no-daemon', 'assembleRelease', f'-Pandroid.injected.signing.store.file={key}', f'-Pandroid.injected.signing.store.password={value(prefix,"STORE_PASSWORD")}', f'-Pandroid.injected.signing.key.alias={value(prefix,"KEY_ALIAS")}', f'-Pandroid.injected.signing.key.password={value(prefix,"KEY_PASSWORD")}', cwd=source/'android')
        apk = source/'android/app/build/outputs/apk/release/app-release.apk'
        if subprocess.check_output(['apkanalyzer','manifest','application-id',str(apk)], text=True).strip() != package: raise RuntimeError('unexpected Android package')
        run('apksigner', 'verify', '--verbose', str(apk)); sha=subprocess.check_output(['git','rev-parse','--short=12','HEAD'],cwd=source,text=True).strip()
        output=WORK/f'{app}-v{cfg["expo"]["version"]}-b{os.environ["VERSION_CODE"]}-{sha}.apk'; shutil.copy2(apk,output); return output
    finally: key.unlink(missing_ok=True)

def publish(apks):
    env={**os.environ,'GH_TOKEN':os.environ['APK_RELEASE_TOKEN']}; repo='ZeloCare/zelocare-apks'; tag=f'build-{os.environ["BUILD_ID"]}'
    run('gh','release','create',tag,*map(str,apks),'--repo',repo,'--title',f'ZeloCare APKs · {os.environ["BUILD_ID"]}','--generate-notes',env=env)
    latest=[]
    for apk in apks:
        out=WORK/f'{apk.name.split("-v")[0]}-latest.apk'; shutil.copy2(apk,out); latest.append(out)
    if subprocess.run(['gh','release','view','latest','--repo',repo],env=env).returncode: run('gh','release','create','latest','--repo',repo,'--title','ZeloCare APKs · latest','--notes','Downloads internos mais recentes.',env=env)
    run('gh','release','upload','latest',*map(str,latest),'--clobber','--repo',repo,env=env)

if __name__ == '__main__':
    os.environ.setdefault('VERSION_CODE',str(int(time.time()))); selected=os.environ['BUILD_APP']
    targets=[]
    if selected in ('all','zelocare-mobile'): targets.append(('zelocare-mobile',os.environ['MOBILE_REF']))
    if selected in ('all','zelocare-volunteer'): targets.append(('zelocare-volunteer',os.environ['VOLUNTEER_REF']))
    publish([build(*target) for target in targets])
