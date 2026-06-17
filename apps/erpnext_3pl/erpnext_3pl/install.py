def after_install():
    from erpnext_3pl.bootstrap.site import main

    main()
