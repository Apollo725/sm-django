from setuptools import setup, find_packages


requirements = [r.strip() for r in open('requirements.txt').readlines()]


setup(
    name='sm',
    author='gappsexperts-lab',
    license='private',
    install_requires=requirements,
    description='Subscription Manager',
    packages=find_packages(),
    extras_require={'dev': ['ipdb==0.10.3', 'nose==1.3.7', 'django-nose==1.4.5', 'factory-boy==2.9.2',
                            'django-pdb==0.6.1']},
    classifiers=['Programming Language :: Python :: 2.7'],
    zip_safe=False,
    include_package_data=True
)
