/**
 * Copyright 2020 Huawei Technologies Co., Ltd
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#ifndef MINDSPORE_LITE_SRC_RUNTIME_KERNEL_ARM_NNACL_INT8_RELU_INT8_H_
#define MINDSPORE_LITE_SRC_RUNTIME_KERNEL_ARM_NNACL_INT8_RELU_INT8_H_

#include <math.h>
#include "nnacl/op_base.h"
#include "nnacl/errorcode.h"
#include "nnacl/quantization/fixed_point.h"
#include "nnacl/quantization/quantize.h"

typedef struct ReluXQuantArg {
  QuantArg input_arg;
  QuantArg output_arg;
  int input_multiplier_;
  int left_shift_;
  int right_shift_;
  int quantized_output_min;
  int quantized_output_max;
} ReluXQuantArg;

#ifdef __cplusplus
extern "C" {
#endif
inline void ReluXInt8(const int8_t *src, int length, int8_t *dst, ReluXQuantArg *arg) {
  for (int i = 0; i < length; ++i) {
    if (src[i] <= arg->input_arg.zp_) {
      dst[i] = arg->output_arg.zp_;
      continue;
    }
    const int32_t input_val = src[i] - arg->input_arg.zp_;
    const int32_t scaled_input = SaturatingRoundingDoublingHighMul(input_val, arg->input_multiplier_);
    const int32_t shifted_input = RoundingDivideByPOT(scaled_input * (1 << arg->left_shift_), -arg->right_shift_);
    const int32_t output = shifted_input + arg->output_arg.zp_;
    dst[i] = (int8_t)MSMIN(output, arg->quantized_output_max);
  }
}
#ifdef __cplusplus
}
#endif

#endif  // MINDSPORE_LITE_SRC_RUNTIME_KERNEL_ARM_NNACL_INT8_RELU_INT8_H_
