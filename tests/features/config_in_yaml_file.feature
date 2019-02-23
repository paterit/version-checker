Feature: Keep version configuration in file
  In order to keep versions configuration in text file
  As a maintainer
  I want to be able to read and save configs in YAML file

  Scenario: Read configuartion from YAML file
     Given YAML file with components configuration
      When program is started without params
      Then checking for new version is done for all components from file