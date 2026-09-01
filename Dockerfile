FROM eclipse-temurin:17-jdk-jammy
ENV DEBIAN_FRONTEND=noninteractive ANDROID_HOME=/opt/android-sdk ANDROID_NDK_HOME=/opt/android-sdk/ndk/26.1.10909125 PATH=/opt/android-sdk/cmdline-tools/latest/bin:/opt/android-sdk/platform-tools:$PATH
RUN apt-get update && apt-get install -y --no-install-recommends curl git unzip ca-certificates gh python3 make g++ \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get update && apt-get install -y --no-install-recommends nodejs \
 && mkdir -p /opt/android-sdk/cmdline-tools \
 && curl -fsSL https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip -o /tmp/android.zip \
 && unzip -q /tmp/android.zip -d /opt/android-sdk/cmdline-tools \
 && mv /opt/android-sdk/cmdline-tools/cmdline-tools /opt/android-sdk/cmdline-tools/latest && rm /tmp/android.zip \
 && yes | sdkmanager --licenses >/dev/null \
 && sdkmanager "platform-tools" "platforms;android-35" "build-tools;35.0.0" "ndk;26.1.10909125" "cmake;3.22.1" \
 && npm install -g expo@latest eas-cli@latest && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
