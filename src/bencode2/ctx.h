#pragma once
#define FMT_HEADER_ONLY

#include <string>
#include <unordered_set>

#include <fmt/core.h>

#include "common.h"

#define defaultBufferSize 4096

class BufferAllocFailed : std::bad_alloc {
  const char *what() const throw() {
    return "failed to alloc member for buffer";
  }
};

class Context {
public:
  char *buf;
  size_t index;
  size_t cap;

  std::unordered_set<uintptr_t> seen;

  Context() {
    buf = (char *)malloc(defaultBufferSize);
    if (buf == NULL) {
      throw BufferAllocFailed();
    }

    index = 0;
    cap = defaultBufferSize;
  }

  ~Context() {
    debug_print("delete context");
    seen.clear();
    free(buf);
  }

  void reset() {
    index = 0;
    seen.clear();
  }

  void write(std::string ss) { write(ss.data(), ss.size()); }

  void write(const char *data, HPy_ssize_t size) {
    bufferGrow(size);

    std::memcpy(buf + index, data, size);

    index = index + size;
  }

  void writeSize_t(size_t val) { write(fmt::format("{}", val)); }

  void writeLongLong(long long val) { write(fmt::format("{}", val)); }

  void writeChar(const char c) {
    bufferGrow(1);
    buf[index] = c;
    index = index + 1;
  }

private:
  void bufferGrow(HPy_ssize_t size) {
    if (size + index + 1 >= cap) {
      char *tmp = (char *)realloc(buf, cap * 2 + size);
      if (tmp == NULL) {
        throw BufferAllocFailed();
      }
      cap = cap * 2 + size;
      buf = tmp;
    }
  }
};
