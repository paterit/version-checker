Feature: Verify if there are new version of component
  In order to have up to date components in the project
  As a maintainer
  I want to verify if new version of component is avialble

  Scenario Outline: Check new version of component
     Given Component with <component_type>, <repo_name>, <component_name> and <version> as parameters
      When check version script is run
      Then there is <response> in response


  Examples: Components versions
     | component_type | repo_name | component_name | version  | response               |
     | docker-image   | nicolargo | glances        | v2.0.0   | 1 components to update |
     | docker-image   | nicolargo | glances        | v100.0.0 | 0 components to update |
     | pypi           | None      | Django         | 2.0.0    | 1 components to update |
     | pypi           | None      | Django         | 100.0.0  | 0 components to update |
