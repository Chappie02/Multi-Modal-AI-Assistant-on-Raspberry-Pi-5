import threading
import logging
import queue
import time

from controller import Controller
from hardware.animation import AnimationManager
from hardware.buttons import ButtonListener, ButtonEvent
from hardware.oled import OledDisplay


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main() -> None:
    setup_logging()
    log = logging.getLogger("main")

    try:
        event_queue: "queue.Queue[ButtonEvent]" = queue.Queue()

        oled = OledDisplay()
        animation = AnimationManager(oled)
        controller = Controller(oled=oled, animation=animation, event_queue=event_queue)

        animation_thread = threading.Thread(
            target=animation.run, name="animation-thread", daemon=True
        )
        animation_thread.start()

        button_listener = ButtonListener(event_queue=event_queue)
        button_thread = threading.Thread(
            target=button_listener.run, name="button-thread", daemon=True
        )
        button_thread.start()

        log.info("Assistant started. Waiting for events.")

        while True:
            try:
                event = event_queue.get()
                controller.handle_event(event)
            except Exception as e:
                log.exception("Unhandled error in main loop: %s", e)
                # Always try to return to idle animation
                try:
                    animation.resume()
                except Exception:
                    pass
                time.sleep(0.1)
    except KeyboardInterrupt:
        log.info("Shutting down (KeyboardInterrupt).")
    except Exception as e:
        log.exception("Fatal error in main: %s", e)


if __name__ == "__main__":
    main()

