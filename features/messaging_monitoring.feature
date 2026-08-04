Feature: Messaging Monitoring
  @Cucumber
  Scenario: CN OTA update and verification
    Given the MQTT collector is running
    And the 0.73 OTA command is sent to the cable node
    When the messages are published to the topic for the past 20 minutes
    Then FirmwareVersionV1 message is sent by the cable node with OTA success status
    And stats detail should contain 0.73 firmware

  @Cucumber
  Scenario: Monitor PLENUM cable messages for 5 minutes
    Given the MQTT collector is running
    When the messages are published to the topic for the past 5 minutes
    Then the messages should be logged
    And the messages should be verified for every minute in the last 5 minutes

  @Cucumber
  Scenario: Monitor HEADSPACE cable messages for 30 minutes
    Given the MQTT collector is running
    When the messages are published to the topic for the past 30 minutes
    Then the messages should be logged
    And the HEADSPACE cable messages should be verified for every 10 minutes in the last 30 minutes

  @Cucumber
  Scenario: Monitor hourly messages for 1 hour
    Given the MQTT collector is running
    When the messages are published to the topic for the past 1 hour
    Then the messages should be logged
    And the hourly messages should be verified for every hour in the last 1 hour

  @Cucumber
  Scenario: Verify EPIQ+ primary cable amount
    Given the MQTT collector is running
    When the messages are published to the topic for the past 1 hour
    Then the EPIQ+ primary cable amount should equal to 4
    And the combination is 2 temperature and 2 omni cables

  @Cucumber
  Scenario: Verify the FN is connected to the primary cable node
    Given the MQTT collector is running
    When the messages are published to the topic for the past 1 hour
    Then the FN should be connected