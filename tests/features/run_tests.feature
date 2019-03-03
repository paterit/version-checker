Feature: Run tests after updating component
  In oreder to make sure that new version of the component doesn't break stuff
  As a maintainer
  I want test to be run after each component version change

  Scenario: Update version in defined files for component
     Given New version of component is set in defined files
      When script is run in update mode with test parameter
      Then run test command and stop in case of failure