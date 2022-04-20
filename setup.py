from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(name='aliot_1',
          author=['Mathis Laroche', 'Enric Soldevila'],
          version='0.1.0',
          description='python IOT library compatible with the ALIVE ecosystem',
          packages=find_packages(
              include=['aliot_1.', 'aliot_1.*']),
          install_requires=[
              'msgpack',
              'schedule',
              'websocket-client'
          ],
          setup_requires=['flake8', 'autopep8']
          )
