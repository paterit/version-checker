Feature: Verify if there are new version of docker image
  In order to have up to date docker images in the project
  As a maintainer
  I want to verify if new version of docker image is avialble

  @wip
  Scenario: Check new version of docker image
    Given Docker image name "glances" and version "v.2.0.0" as parameters
    When check version script is run
    Then there is "new version found" in response
