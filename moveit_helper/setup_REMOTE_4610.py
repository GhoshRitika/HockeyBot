from setuptools import setup

package_name = 'moveit_helper'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='avaz',
    maintainer_email='AvaZahedi2023@u.northwestern.edu',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': ['move_action_intercept=intercept.move_action_intercept:interept_entry',
                            'ik_hanyin_intercept=moveit_helper.ik_hanyin_intercept:interept_entry'
        ],
    },
)