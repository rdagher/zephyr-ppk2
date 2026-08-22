# Include path is unconditional so instrumented code still compiles
# with CONFIG_PPK2_TRACE=n (the header stubs itself out).
zephyr_include_directories(include)

# Route each listed function through its PPK2_TRACE_WRAP wrapper.
# No-op with CONFIG_PPK2_TRACE=n (the stub wrappers pass through).
function(ppk2_trace_wrap)
  if(CONFIG_PPK2_TRACE)
    foreach(fn ${ARGV})
      zephyr_ld_options(-Wl,--wrap=${fn})
    endforeach()
  endif()
endfunction()

if(CONFIG_PPK2_TRACE)
  zephyr_linker_sources(SECTIONS linker/sections-rom.ld)
endif()

if(CONFIG_PPK2_TRACE_AUTO_INIT)
  zephyr_library()
  zephyr_library_sources(src/ppk2_trace_init.c)
endif()
