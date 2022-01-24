[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Foddstr13%2Fjellyfin-plugin-repository-manager.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2Foddstr13%2Fjellyfin-plugin-repository-manager?ref=badge_shield)

Installing
==========
From PyPI
---------
```bash
pip install --user jprm
```

From GitHub
-----------
```
pip install --user git+https://github.com/oddstr13/jellyfin-plugin-metadata-manager
```

From local developement directory
---------------------------------
```
git clone https://github.com/oddstr13/jellyfin-plugin-metadata-manager.git
pip install --user --editable jellyfin-plugin-metadata-manager
```

Stand-alone Python script
-------------------------
```
wget -O jprm.py https://raw.githubusercontent.com/oddstr13/jellyfin-plugin-repository-manager/master/jprm/__init__.py
```

Examples
========

Running jprm
------------

```
jprm --version
```

```
python3 -m jprm --version
```

```
python3 jprm.py --version
```

Initializing plugin repository
------------------------------

```
mkdir -p /path/to/repo
jprm repo init /path/to/repo
```

See [build_plugin.sh](https://github.com/oddstr13/jellyfin-plugin-repository-manager/blob/master/build_plugin.sh) for an example script.


## License
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Foddstr13%2Fjellyfin-plugin-repository-manager.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2Foddstr13%2Fjellyfin-plugin-repository-manager?ref=badge_large)