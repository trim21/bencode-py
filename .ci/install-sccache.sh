set -ex

sccache_version=0.8.2

cd /tmp

# Install sccache
curl -sSL https://github.com/mozilla/sccache/releases/download/v${sccache_version}/sccache-v${sccache_version}-$(arch)-unknown-linux-musl.tar.gz \
  -o sccache-v${sccache_version}-$(arch)-unknown-linux-musl.tar.gz

tar -zxf sccache-v${sccache_version}-$(arch)-unknown-linux-musl.tar.gz

cp sccache-v${sccache_version}-$(arch)-unknown-linux-musl/sccache /usr/bin

sccache --show-stats
