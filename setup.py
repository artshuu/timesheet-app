from setuptools import setup, find_packages

setup(
    name="timesheet-tech-dept",
    version="1.0.0",
    # Явно указываем, что пакеты находятся внутри папки src
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
