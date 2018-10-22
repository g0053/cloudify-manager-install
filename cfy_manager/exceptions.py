#########
# Copyright (c) 2017 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.


class BootstrapError(StandardError):
    pass


class FileError(BootstrapError):
    pass


class NetworkError(BootstrapError):
    pass


class ValidationError(BootstrapError):
    pass


class InputError(BootstrapError):
    pass


class ProcessExecutionError(BootstrapError):
    def __init__(self, message, return_code=None):
        self.return_code = return_code
        super(ProcessExecutionError, self).__init__(message)
