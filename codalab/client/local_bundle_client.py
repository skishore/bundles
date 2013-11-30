from codalab.bundles import get_bundle_subclass
from codalab.bundles.uploaded_bundle import UploadedBundle
from codalab.common import CODALAB_HOME
from codalab.client.bundle_client import BundleClient
from codalab.lib.bundle_store import BundleStore
from codalab.lib import (
  canonicalize,
  path_util,
)
from codalab.model.util import get_codalab_model


class LocalBundleClient(BundleClient):
  def __init__(self, codalab_home=None):
    codalab_home = codalab_home or CODALAB_HOME
    self.bundle_store = BundleStore(codalab_home)
    self.model = get_codalab_model(codalab_home)

  def get_spec_uuid(self, bundle_spec):
    return canonicalize.get_spec_uuid(self.model, bundle_spec)

  def upload(self, bundle_type, path, metadata):
    bundle_subclass = get_bundle_subclass(bundle_type)
    if not issubclass(bundle_subclass, UploadedBundle):
      raise ValueError('Tried to upload %s!' % (bundle_subclass.__name__,))
    # Type-check the bundle metadata BEFORE uploading the bundle data.
    # This optimization will avoid file operations on failed bundle creations.
    bundle_subclass.construct(data_hash='', metadata=metadata).validate()
    data_hash = self.bundle_store.upload(path)
    bundle = bundle_subclass.construct(data_hash=data_hash, metadata=metadata)
    self.model.save_bundle(bundle)
    return bundle.uuid

  def make(self, targets):
    bundle_subclass = get_bundle_subclass('make')
    bundle = bundle_subclass.construct(targets)
    self.model.save_bundle(bundle)
    return bundle.uuid

  def run(self, program_uuid, targets, command):
    bundle_subclass = get_bundle_subclass('run')
    bundle = bundle_subclass.construct(program_uuid, targets, command)
    self.model.save_bundle(bundle)
    return bundle.uuid

  def info(self, uuid):
    bundle = self.model.get_bundle(uuid)
    return {
      'bundle_type': bundle.bundle_type,
      'uuid': bundle.uuid,
      'location': self.bundle_store.get_location(bundle.data_hash),
      'metadata': bundle.metadata.to_dict(),
      'state': bundle.state,
    }

  def ls(self, target):
    path = canonicalize.get_target_path(self.bundle_store, self.model, target)
    return path_util.ls(path)
