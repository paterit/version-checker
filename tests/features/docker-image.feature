Feature: Verify if there are new version of docker image
  In order to have up to date docker images in the project
  As a maintainer
  I want to verify if new version of docker image is avialble

  Scenario Outline: Check new version of docker image
    Given Docker image name <repo_name>/<component> and <version> as parameters
    When check version script is run
    Then there is <response> in response


  Examples: Docker images versions
     | repo_name | component | version | response |
     | nicolargo | glances   | v2.0.0  | new version found |
     | nicolargo | glances   | v100.0.0 | no newer version found |