# Headless Minecraft client for scripts/smoke-test-client.sh: Java 21 + Xvfb + Mesa (llvmpipe) + portablemc.
FROM docker.io/library/eclipse-temurin:21-jdk-noble
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      xvfb xauth libgl1 libgl1-mesa-dri libegl1 libglx-mesa0 libxrandr2 libxxf86vm1 libxcursor1 libxi6 libxtst6 \
      libasound2t64 libpulse0 python3 python3-pip ca-certificates curl \
 && pip3 install --break-system-packages --no-cache-dir portablemc==5.0.6 \
 && rm -rf /var/lib/apt/lists/*
