

if __name__ == '__main__':

    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    from spimagine.spimagine_gui import main


    main()
