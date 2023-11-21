# Cython Project Template
A simple project file structure to quickly ramp-up a new Cython project.

## Contribute
Let's work to make it as easy as possible for folks to create new Cython-based projects.
Pull-Requests, Issues, and Feedback are all welcome on the project's [GitHub Page](https://github.com/jrenaud90/CythonProjectTemplate)

## Change Right Away
- Update the `LICENSE.md` to match your project's needs.
- Update `pyproject.toml` with your project & author information, dependencies, etc.
- Change the directory `CythonProjectTemplate` to match the name of your package.
- Search for `"#! Update"` in all files to find critical locations that need to be changed for your specific project.
- Read through `.github\workflows\build_wheels_main_pypi.yml` and make the necessary changes.
- `.gitignore` was configured with Cython, Python, C, C++, in mind. Also it has VSCode IDE specific file ignores. You may need to edit for your needs.

## Developing Your Project
- Whenever you create a new cython pyx/pxd file make sure to add it to the `cython_extensions.json` file otherwise it will not be compiled when your project is installed.
