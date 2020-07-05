```
VERSION=4.0.$(date -u +%Y%m%d.%H%M%S)

zip=$(python3 jprm.py plugin build jellyfin-plugin-bookshelf/ --output=artifacts --version=$VERSION)

mkdir -p test
python3 jprm.py repo init test

python3 jprm.py repo add --url=https://example.com/repo/test test $zip
```
