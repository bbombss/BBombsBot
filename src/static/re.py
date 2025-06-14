__all__ = [
    "FAKE_URL_REGEX",
    "FORMATTING_REGEX",
    "HYPERLINK_REGEX",
    "INVITE_REGEX",
    "URL_REGEX",
]

import re

URL_REGEX = re.compile(r"(http|https:\/\/)([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])")
INVITE_REGEX = re.compile(r"(https?:\/\/)?(www.)?(discord.(gg|io|me|li)|discordapp.com\/invite)\/[^\s\/]+?(?=\b)")
HYPERLINK_REGEX = re.compile(r"\[\S.*?\]\((https|http):\/\/\S.*?\)")
FAKE_URL_REGEX = re.compile(r"\[\S*?\.\S{2,63}\]\((https|http):\/\/\S.*?\)")
FORMATTING_REGEX = re.compile(r"<[:|id|t|@|a:|#]\S+>")


# Copyright (C) 2025 BBombs

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
