"""Explicit CPU-only batch fixture, never a real Wan/GPU acceptance."""

import copy
import time

from g2.latent_cache.batch_contract import ENCODER_SCHEMA, NUMERICS


class FakeBatchEncoder:
    def __init__(self, *, delay=0, offset=0):
        self.delay, self.offset, self.calls = delay, offset, 0

    def descriptor(self):
        return dict(
            schema=ENCODER_SCHEMA,
            implementation="TEST_ONLY_CPU_BATCH",
            test_only=True,
            max_batch_size=32,
            numerics=copy.deepcopy(NUMERICS),
        )

    def encode_batch(self, images, preprocessing):
        import torch

        from g2.latent_cache.encoding import preprocess_rgb

        self.calls += 1
        time.sleep(self.delay)
        results = []
        for position, image in enumerate(images):
            _, prep = preprocess_rgb(image, preprocessing)
            # Deliberate dependence on actual batch and order catches silent
            # resize, single-image fallback and numerical-context relabeling.
            latent = torch.full(
                (48, 16, 16),
                float(image[0, 0, 0]) / 255
                + len(images) / 100
                + position / 1000
                + self.offset,
                dtype=torch.float32,
            )
            prep.update(
                vae_input_shape=[len(images), 3, 1, 256, 256],
                latent_shape=[48, 16, 16],
                latent_dtype="float32",
                latent_mask_basis="CONTENT_RECT_ONLY_RECEPTIVE_FIELD_NOT_CERTIFIED",
                storage_conversion=dict(
                    from_dtype="float32",
                    to_dtype="float32",
                    exact=True,
                    max_abs_error=0.0,
                ),
            )
            results.append((latent, prep))
        self.last_metrics = dict(
            native_input_shape=[len(images), 3, 1, 256, 256],
            native_calls=1,
            native_cuda_ms=None,
            peak_allocated_bytes=0,
            peak_reserved_bytes=0,
        )
        return results
