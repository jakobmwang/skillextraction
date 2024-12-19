SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


CREATE TABLE `joburls` (
  `id` int(10) UNSIGNED NOT NULL,
  `source` varchar(25) NOT NULL,
  `url` varchar(255) NOT NULL,
  `added` datetime NOT NULL DEFAULT current_timestamp(),
  `crawled` datetime DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


ALTER TABLE `joburls`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `url` (`url`) USING HASH,
  ADD KEY `source` (`source`,`crawled`,`added`) USING BTREE;


ALTER TABLE `joburls`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;


CREATE TABLE `jobads` (
  `id` int(10) UNSIGNED NOT NULL,
  `source` varchar(25) NOT NULL,
  `url` varchar(255) NOT NULL,
  `real_url` varchar(255) NOT NULL,
  `title` varchar(255) NOT NULL,
  `company` varchar(255) NOT NULL,
  `location` varchar(255) NOT NULL,
  `category` varchar(255) NOT NULL,
  `content` text NOT NULL,
  `published` date NOT NULL,
  `crawled` datetime DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


ALTER TABLE `jobads`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `url` (`url`) USING HASH,
  ADD KEY `crawled` (`crawled`);


ALTER TABLE `jobads`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;
