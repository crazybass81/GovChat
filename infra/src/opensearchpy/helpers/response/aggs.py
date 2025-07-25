# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.
#
# Modifications Copyright OpenSearch Contributors. See
# GitHub history for details.
#
#  Licensed to Elasticsearch B.V. under one or more contributor
#  license agreements. See the NOTICE file distributed with
#  this work for additional information regarding copyright
#  ownership. Elasticsearch B.V. licenses this file to you under
#  the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
# 	http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing,
#  software distributed under the License is distributed on an
#  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#  KIND, either express or implied.  See the License for the
#  specific language governing permissions and limitations
#  under the License.

from typing import Any

from ..utils import AttrDict, AttrList
from . import AggResponse, Response


class Bucket(AggResponse):
    def __init__(self, aggs: Any, search: Any, data: Any, field: Any = None) -> None:
        super(Bucket, self).__init__(aggs, search, data)


class FieldBucket(Bucket):
    def __init__(self, aggs: Any, search: Any, data: Any, field: Any = None) -> None:
        if field:
            data["key"] = field.deserialize(data["key"])
        super(FieldBucket, self).__init__(aggs, search, data, field)


class BucketData(AggResponse):
    _bucket_class = Bucket

    def _wrap_bucket(self, data: Any) -> Any:
        return self._bucket_class(
            self._meta["aggs"],
            self._meta["search"],
            data,
            field=self._meta.get("field"),
        )

    def __iter__(self) -> Any:
        return iter(self.buckets)

    def __len__(self) -> int:
        return len(self.buckets)

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, (int, slice)):
            return self.buckets[key]
        return super(BucketData, self).__getitem__(key)

    @property
    def buckets(self) -> Any:
        if not hasattr(self, "_buckets"):
            field = getattr(self._meta["aggs"], "field", None)
            if field:
                self._meta["field"] = self._meta["search"]._resolve_field(field)
            bs = self._d_["buckets"]
            if isinstance(bs, list):
                bs = AttrList(bs, obj_wrapper=self._wrap_bucket)
            else:
                bs = AttrDict({k: self._wrap_bucket(bs[k]) for k in bs})
            super(AttrDict, self).__setattr__("_buckets", bs)
        return self._buckets


class FieldBucketData(BucketData):
    _bucket_class = FieldBucket


class TopHitsData(Response):
    def __init__(self, agg: Any, search: Any, data: Any) -> None:
        super(AttrDict, self).__setattr__("meta", AttrDict({"agg": agg, "search": search}))
        super(TopHitsData, self).__init__(search, data)


__all__ = ["AggResponse"]
