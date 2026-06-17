from setuptools import find_packages, setup


with open("requirements.txt") as f:
    install_requires = f.read().strip().splitlines()


setup(
    name="erpnext_3pl",
    version="0.1.0",
    description="Warehouse-first 3PL extensions for ERPNext",
    author="ERPNext 3PL Platform",
    author_email="noreply@example.invalid",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
