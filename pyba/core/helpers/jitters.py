import asyncio
import random
from typing import List

from playwright.async_api import Page


class MouseMovements:
    """
    Class to handle random mouse movements in pyba

    These functions need to be happening async to actions such as waiting for page to load. This class
    will replace all `time.sleep()`, `asyncio.sleep()` and `wait_for_*` functionality.

    The movements are deliberately constrained to a specific region in the viewport.

    For more information on the algorithms, check out https://github.com/oxylabs/OxyMouse
    """

    def __init__(self, page: Page, width: int = 1200, height: int = 1024):
        """
        Args:
            `page`: The current page object
            `width`: The viewport width for the session, defaults at 1200
            `height`: The viewport height for the session, defaults at 1024
        """
        self.page = page

        # Picks a random number between 0 and the viewport values with mode as 500
        self.width = int(random.triangular(0, width, 600))
        self.height = int(random.triangular(0, height, 512))

    async def _run(self, algorithm: str):
        """
        Runs the mouse movements for a specified algorithm

        (NOTE: This is constrained to a small window)
        """
        from oxymouse import OxyMouse

        mouse = OxyMouse(algorithm=algorithm)
        movements = mouse.generate_random_coordinates(
            viewport_width=self.width,
            viewport_height=self.height,
        )

        for x, y in movements:
            await self.page.mouse.move(int(x), int(y), steps=10)
            await asyncio.sleep(random.uniform(0.004, 0.015))

    async def bezier_movements(self):
        """
        Function to perform bezier curve movements
        """
        await self._run(algorithm="bezier")

    async def gaussian_movements(self):
        """
        Function to perform gaussian movements
        """
        await self._run(algorithm="gaussian")

    async def perlin_movements(self):
        """
        Function to perform perlin movements
        """

        await self._run(algorithm="perlin")

    async def random_movement(self):
        """
        Chooses a function at random
        """

        mapping = {
            1: self.bezier_movements,
            2: self.gaussian_movements,
            3: self.perlin_movements,
        }

        _ = mapping[random.randint(1, 3)]
        await _()


class ScrollMovements:
    """
    Class to mimic realistic scroll movements
    """

    def __init__(self, page: Page):
        self.page = page

    def generate_scroll_values(
        self,
        num_steps: int = 15,
        max_delta: int = 100,
        min_delta: int = 15,
    ) -> List[int]:
        """
        Helper function to generate random scroll values that sum up to zero.

        Returns a list with scroll values in pixels, positive being downscroll
        and negative being an upscroll. The final sum should be 0.
        """

        # An odd number of steps>=3 is good for jitters
        if num_steps <= 1 or num_steps % 2 != 1:
            num_steps = 15

        scroll_values: List[int] = []
        current_sum = 0

        # Generate N-1 steps randomly
        # We constrain the steps to an odd number (N-1 is even) to ensure
        # we have a balanced number of positive/negative steps, which helps
        # keep the final step small and the list sum close to zero.
        # Total number of pairs (down/up movements)
        num_pairs = (num_steps - 1) // 2

        # Generate positive (down) movements
        for _ in range(num_pairs):
            delta = random.randint(min_delta, max_delta)
            scroll_values.append(delta)
            current_sum += delta

        # Generate negative (up) movements
        for _ in range(num_pairs):
            delta = random.randint(-max_delta, -min_delta)
            scroll_values.append(delta)
            current_sum += delta

        # Adding the final step to balance the list to zero
        # This is the "jitter" that returns the scroll position to the start point
        final_delta = -current_sum
        scroll_values.append(final_delta)

        # Randomly shuffling the scroll values again
        random.shuffle(scroll_values)

        return scroll_values

    async def apply_scroll_jitters(
        self,
        num_steps: int = 15,
        max_delta: int = 100,
        min_delta: int = 15,
    ):
        """
        Performs the scroll jitters using the generated values.
        """
        scroll_values = self.generate_scroll_values(
            num_steps=num_steps,
            max_delta=max_delta,
            min_delta=min_delta,
        )

        for delta in scroll_values:
            await self.page.mouse.wheel(0, delta)
            # Adding a random delay in between
            await asyncio.sleep(random.uniform(0.05, 0.2))
