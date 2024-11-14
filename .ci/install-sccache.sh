set -ex

mkdir /tmp/ -p

curl -sSL https://github.com/mozilla/sccache/releases/download/v0.8.2/sccache-dist-v0.8.2-x86_64-unknown-linux-musl.tar.gz \
  -o /tmp/sccache.tar.gz

tar -xvf /tmp/sccache.tar.gz -C /tmp/

mv /tmp/sccache-dist-v0.8.2-x86_64-unknown-linux-musl/sccache-dist /bin/sccache
