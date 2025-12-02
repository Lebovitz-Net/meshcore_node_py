# Project File Structure

│—— .git
│  │—— hooks
│  │  │—— applypatch-msg.sample
│  │  │—— commit-msg.sample
│  │  │—— fsmonitor-watchman.sample
│  │  │—— post-update.sample
│  │  │—— pre-applypatch.sample
│  │  │—— pre-commit.sample
│  │  │—— pre-merge-commit.sample
│  │  │—— pre-push.sample
│  │  │—— pre-rebase.sample
│  │  │—— pre-receive.sample
│  │  │—— prepare-commit-msg.sample
│  │  │—— push-to-checkout.sample
│  │  │—— sendemail-validate.sample
│  │  ╵—— update.sample
│  │—— info
│  │  ╵—— exclude
│  │—— logs
│  │  │—— refs
│  │  │  │—— heads
│  │  │  │  │—— main
│  │  │  │  ╵—— master
│  │  │  ╵—— remotes
│  │  │  │  ╵—— origin
│  │  │  │  │  │—— main
│  │  │  │  │  ╵—— master
│  │  ╵—— HEAD
│  │—— objects
│  │  │—— 03
│  │  │  ╵—— e079a7c573f8bd3be0ceb4aca93f551a7fb5ad
│  │  │—— 07
│  │  │  ╵—— 4f4d62d123e07ecc45d8865bc35129a2938f0f
│  │  │—— 0c
│  │  │  │—— c4e51dc45d31a6fb4e4e85dfd1c0bc2e4cf445
│  │  │  ╵—— efee5217ced53ea8d92f6b4e372129f4551eb0
│  │  │—— 13
│  │  │  ╵—— 7b5cf9606efecd95d7021910ff6b25bfdc8077
│  │  │—— 18
│  │  │  ╵—— 9cba373c1ff54299491bf855540950f49e75b5
│  │  │—— 34
│  │  │  ╵—— fb93d077e7cbd127a22a03f9ca78d13a51f848
│  │  │—— 37
│  │  │  ╵—— 618463f054b46e2f8c4555f6639da97cf7679a
│  │  │—— 38
│  │  │  ╵—— 097e72d044d56b96a335f3d06f8970dce2fa32
│  │  │—— 3f
│  │  │  ╵—— 72bfd40b564756feffeab80b87a3719b25f7c4
│  │  │—— 40
│  │  │  │—— 6fd33ec6697a396d587ddfac21927b08924d0e
│  │  │  ╵—— ee42df716c328c66ede88116452b447fed01cc
│  │  │—— 41
│  │  │  ╵—— 536a19d37966e0e2b178886bcc98a949424d71
│  │  │—— 49
│  │  │  ╵—— 1c67abf132ba892d6d7d2dd846dee932ea85b7
│  │  │—— 63
│  │  │  ╵—— 16b486090ef0b5f2fab688f96d03bd267c9ae0
│  │  │—— 67
│  │  │  ╵—— 517c66be503d66a4d21b1fb0d1b215419f22e4
│  │  │—— 7b
│  │  │  ╵—— 989964cb91c7af6ab777cd12ca1bf4fd034c4d
│  │  │—— 7f
│  │  │  ╵—— 50afeb42835186c3a39a58223977dc14986acc
│  │  │—— 82
│  │  │  ╵—— c42aee1df5475979b5d000e65f0a17fa932372
│  │  │—— 84
│  │  │  ╵—— a143a81daebfda92445e5694a8ee29918290cf
│  │  │—— 8b
│  │  │  ╵—— eaf333bf5f411c94254097155b17c611b4d223
│  │  │—— 8c
│  │  │  ╵—— 4e9bb1c00b88a1eb72ff30e6e606dee94b87b4
│  │  │—— 90
│  │  │  ╵—— df0e1ef7c8a9dbda02fcaf2471085a96cff5a0
│  │  │—— 9f
│  │  │  ╵—— 0ebf6b4dff6cf58095da6055b19e8895eb8a31
│  │  │—— a0
│  │  │  ╵—— d110e97121f723cc08150ba6d84dfca7300bea
│  │  │—— a1
│  │  │  ╵—— e4dc5f51eb9e2d69c241197d7ad3e28cf7c1ce
│  │  │—— a4
│  │  │  ╵—— 329afae0edd6388532d002a368abac36e843cd
│  │  │—— a6
│  │  │  ╵—— 8dd606d59a825f5d7ee8bad0e32e9ba55ef213
│  │  │—— a8
│  │  │  ╵—— 2496acb691160f485196893587f958c24dd4d8
│  │  │—— ac
│  │  │  ╵—— fc36f90ffb54cc1d994a23450514b4d7e00353
│  │  │—— b1
│  │  │  ╵—— 1e67a1a90ecf15eae04b449b6c9dce0a20288b
│  │  │—— bc
│  │  │  ╵—— 82181de72e049287d7ba04a5d6b4a8bda47e01
│  │  │—— bd
│  │  │  ╵—— f259a040ca1d9425c65e4ade4c812229b2ad2a
│  │  │—— c1
│  │  │  ╵—— ac9ef66e146625d9921085032dead49c1d9b7b
│  │  │—— d0
│  │  │  │—— 74bfe600f1c6069cf4caa91558b222dded201a
│  │  │  ╵—— 85f19b2924d935206ce743864087704e57ab06
│  │  │—— d2
│  │  │  ╵—— 923f03797c2112d311d510fce18a8b862ba6de
│  │  │—— d3
│  │  │  ╵—— 9c3a9059d0139253030597168c76e270979914
│  │  │—— e6
│  │  │  ╵—— 9de29bb2d1d6434b8b29ae775ad8c2e48c5391
│  │  │—— f0
│  │  │  ╵—— 1c3ac05846c5db915b27cd70d7b7e0eb819714
│  │  │—— fd
│  │  │  ╵—— 364edb4e130e7775a75cee07ced5193bdea898
│  │  │—— info
│  │  ╵—— pack
│  │—— refs
│  │  │—— heads
│  │  │  │—— main
│  │  │  ╵—— master
│  │  │—— remotes
│  │  │  ╵—— origin
│  │  │  │  │—— main
│  │  │  │  ╵—— master
│  │  ╵—— tags
│  │—— COMMIT_EDITMSG
│  │—— config
│  │—— description
│  │—— HEAD
│  ╵—— index
│—— src
│  │—— buffer
│  │  │—— buffer_reader.py
│  │  │—— buffer_utils.py
│  │  ╵—— buffer_writer.py
│  │—— listener
│  │  │—— LISTENER.md
│  │  │—— node_listener.py
│  │  │—— node_listener.py.txt
│  │  │—— node_transport.py
│  │  │—— serial_node_listener.py
│  │  │—— serial_transport.py
│  │  │—— sx1262_node_listener.py
│  │  │—— sx1262_transport.py
│  │  │—— tcp_node_listener.py
│  │  │—— tcp_transport.py
│  │  ╵—— __init__.py
│  │—— store
│  │  │—— contact_store.py
│  │  ╵—— message_store.py
│  │—— sx1262
│  │  │—— sx1262.py
│  │  ╵—— __init__.py
│  │—— advert.py
│  │—— cayenne_lpp.py
│  │—— constants.py
│  │—— events.py
│  │—— files.txt
│  │—— hendler_maps.py
│  │—— index.py
│  │—— main.py
│  │—— node_manager.py
│  │—— packet.py
│  ╵—— random_utils.py
│—— filestructure.md
│—— filestructure.ps1
│—— meshcore_node_py.code-workspace
╵—— PROTOCOLmd
