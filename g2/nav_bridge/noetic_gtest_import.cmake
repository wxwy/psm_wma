# Optional build configuration for Noetic with CMake >=3.24. Catkin caches
# GTEST_* names; import real targets in every configure before adding tests.
if(CMAKE_VERSION VERSION_GREATER_EQUAL "3.24")
  find_package(GTest CONFIG REQUIRED GLOBAL)
else()
  find_package(GTest REQUIRED)
endif()
