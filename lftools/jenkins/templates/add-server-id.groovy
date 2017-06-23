// @License EPL-1.0 <http://spdx.org/licenses/EPL-1.0>
// #############################################################################
// Copyright (c) 2017, 2018, 2019 The Linux Foundation and others.
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Eclipse Public License v1.0
// which accompanies this distribution, and is available at
// http://www.eclipse.org/legal/epl-v10.html
//
// #############################################################################

import org.jenkinsci.lib.configprovider.model.Config
import org.jenkinsci.plugins.configfiles.maven.MavenSettingsConfig
import org.jenkinsci.plugins.configfiles.maven.security.ServerCredentialMapping
import org.jenkinsci.plugins.configfiles.maven.MavenSettingsConfig.MavenSettingsConfigProvider
import org.jenkinsci.plugins.configfiles.GlobalConfigFiles
import org.jenkinsci.plugins.configfiles.ConfigFileStore

// Function to add a server id to a Maven Settings file
def addServerId = { configFileId, serverId ->
    List<ServerCredentialMapping> mappings
    ServerCredentialMapping mapping
    ConfigFileStore sto = GlobalConfigFiles.get();
    Config c = sto.getById("${configFileId}-settings");
    def string_id = c.name;
    def List<ServerCredentialMapping> map_list = c.serverCredentialMappings;
    println "Adding ${serverId} to ${string_id} settings file: ${configFileId}-setting"
    mappings = new ArrayList<ServerCredentialMapping>();
    mapping = new ServerCredentialMapping(serverId, configFileId);
    mappings.add(mapping);
    map_list.addAll(mappings);
    c.serverCredentialMappings = map_list;
}
