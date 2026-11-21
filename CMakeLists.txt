# SPDX-License-Identifier: Apache-2.0 OR MIT

# Always on the include path: marked code builds with CONFIG_PPK2_TRACE=n too.
zephyr_include_directories(include)

# Route calls to each listed function through its PPK2_TRACE_WRAP wrapper.
function(ppk2_trace_wrap)
  if(CONFIG_PPK2_TRACE)
    foreach(fn ${ARGV})
      zephyr_ld_options(-Wl,--wrap=${fn})
    endforeach()
  endif()
endfunction()

if(CONFIG_PPK2_TRACE)
  zephyr_library()
  zephyr_library_sources(src/ppk2_trace.c)
  zephyr_library_sources_ifdef(CONFIG_PPK2_TRACE_RADIO src/ppk2_trace_radio.c)
  zephyr_linker_sources(SECTIONS linker/sections-rom.ld)
endif()
