Feature: Verify if there are new version of docker image
  In order to have up to date docker images in the project
  As a maintainer
  I want to verify if new version of docker image is avialble

  Scenario: Check new version of docker image
    Given Current version and name of the docker image
    When API to docker repository is called
    Then newest version is returned

  Scenario: Check new version of docker image with filter
    Given Current version and name of the docker image
      and filter for version as a regular experssion
    When API to docker repository is called
    Then new version is returned that fit to filter


  Scenario: Check new version of docker image with exclusions
    Given Current version and name of the docker image
      and a list of excluded versions si given
    When API to docker repository is called
    Then new version is returned that not exits in excluded list