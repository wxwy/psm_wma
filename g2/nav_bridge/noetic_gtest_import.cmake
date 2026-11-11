# Optional build configuration for Noetic with CMake >=3.24. Catkin caches
# GTEST_* names; import real targets in every configure before adding tests.
if(CMAKE_VERSION VERSION_GREATER_EQUAL "3.24")
  find_package(GTest CONFIG REQUIRED GLOBAL)
else()
  find_package(GTest REQUIRED)
endif()

# Older Catkin creates legacy imported libraries whose IMPORTED_LOCATION is
# literally "GTest::gtest" after FindGTest starts returning target names.
# Keep the same installed libraries and repair only that invalid location.
foreach(_g2_test_name IN ITEMS gtest gtest_main)
  if(TARGET ${_g2_test_name} AND TARGET GTest::${_g2_test_name})
    get_target_property(_g2_legacy_imported ${_g2_test_name} IMPORTED)
    get_target_property(_g2_legacy_location ${_g2_test_name} IMPORTED_LOCATION)
    if(_g2_legacy_imported AND _g2_legacy_location MATCHES "^GTest::")
      set(_g2_fixed_location "")
      foreach(_g2_suffix IN ITEMS "" _RELEASE _RELWITHDEBINFO _MINSIZEREL _DEBUG _NOCONFIG)
        get_target_property(_g2_real_location GTest::${_g2_test_name} IMPORTED_LOCATION${_g2_suffix})
        if(_g2_real_location AND EXISTS "${_g2_real_location}")
          set(_g2_fixed_location "${_g2_real_location}")
          break()
        endif()
      endforeach()
      if(NOT _g2_fixed_location)
        message(FATAL_ERROR "Installed GTest library location is unavailable")
      endif()
      set_target_properties(${_g2_test_name} PROPERTIES IMPORTED_LOCATION "${_g2_fixed_location}")
    endif()
  endif()
endforeach()
