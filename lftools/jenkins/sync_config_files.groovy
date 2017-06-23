import org.jenkinsci.lib.configprovider.AbstractConfigProviderImpl
import org.jenkinsci.lib.configprovider.ConfigProvider
import org.jenkinsci.lib.configprovider.model.Config
import org.jenkinsci.lib.configprovider.model.ContentType
import org.jenkinsci.lib.configprovider.model.ContentType.DefinedType
import jenkins.*
import jenkins.model.*
import hudson.*
import hudson.model.*
import org.jenkinsci.plugins.*
import org.jenkinsci.lib.configprovider.model.Config
import hudson.maven.MavenModuleSet
import org.jenkinsci.plugins.configfiles.ConfigFilesManagement
import org.jenkinsci.plugins.configfiles.maven.GlobalMavenSettingsConfig
import org.jenkinsci.plugins.configfiles.maven.GlobalMavenSettingsConfig.GlobalMavenSettingsConfigProvider
import org.jenkinsci.plugins.configfiles.maven.MavenSettingsConfig
import org.jenkinsci.plugins.configfiles.maven.MavenSettingsConfig.MavenSettingsConfigProvider
import com.cloudbees.plugins.credentials.impl.*;
import com.cloudbees.plugins.credentials.*;
import com.cloudbees.plugins.credentials.domains.*;
import org.apache.commons.lang.RandomStringUtils
// Not all these imports are needed, I know.. but as I worked I kept on adding more.. 
// will remove them or simplify them once i am done

def instance = Jenkins.getInstance()
MavenSettingsConfigProvider mavenSettingProvider;
ConfigFilesManagement config_2;
GlobalMavenSettingsConfigProvider globalMavenSettingsConfigProvider;

// Creating the mappings for the ServerIds and Credentials which will be added to the config file
// TODO: Loop through the server IDs and add them since they are always the same
ServerCredentialMapping mapping1 = new ServerCredentialMapping("server1", "3e162fbf-ac39-430b-ae50-937ba25d1a8e");
ServerCredentialMapping mapping2 = new ServerCredentialMapping("server2", "fabric");
ServerCredentialMapping mapping3 = new ServerCredentialMapping("server3", "docker");
List<ServerCredentialMapping> mappings = new ArrayList<ServerCredentialMapping>();
mappings.add(mapping1);
mappings.add(mapping2);
mappings.add(mapping3);

// Adding the config with the mappings
// This will also be in the loop of repos
MavenSettingsConfigProvider mavenSettingsProvider = new MavenSettingsConfigProvider();
MavenSettingsConfig c1 = (MavenSettingsConfig) mavenSettingsProvider.newConfig();
MavenSettingsConfig c2 = new MavenSettingsConfig("latest", "greatest" , c1.comment, c1.content, MavenSettingsConfig.isReplaceAllDefault, mappings);
//MavenSettingsConfigProvider.getInstance().getStore().addConfig(next, dumy);
GlobalConfigFiles globalConfigFiles = new GlobalConfigFiles();
globalConfigFiles.save(c2);

// I did this loop as a test to attempt to create a new config file. 
// I am looping throught the configs, but I need to investigate how to get to the Maven config and just create that one
for (ConfigProvider cp : ConfigProvider.all()) {
    Config config = cp.newConfig("myid", "myname", "mycomment", "mycontent");
    def string_id = config.content;
    println "add! ${string_id}"
}

// Playing with credentials
println "printing credentials ..."

def creds = com.cloudbees.plugins.credentials.CredentialsProvider.lookupCredentials(
    com.cloudbees.plugins.credentials.common.StandardUsernameCredentials.class,
    Jenkins.instance,
    null,
    null
);
for (c in creds) {
     println(c.id + ": " + c.description)
}

// Looks and makes sure if a credential exists or not
def findCredentials = { username ->
    def find_creds = com.cloudbees.plugins.credentials.CredentialsProvider.lookupCredentials(
            com.cloudbees.plugins.credentials.common.StandardUsernamePasswordCredentials.class,
            jenkins.model.Jenkins.instance
            )
  
    def c = find_creds.findResult { it.username == username ? it : null }

    if ( c ) {
        return true
    } else {
        return false
    }
}


println "Loop with credentials"

// I want to get the repos list automatically, I am thinking of an ssh command that generates the output into a file
// For now, I am fiving it a sample...
def projects = ["policy-docker", "policy-common", "policy-engine"]
int randomPasswordLength = 64
String charset = (('a'..'z') + ('A'..'Z') + ('0'..'9')).join()
String randomPassword
boolean credExists = false
Credentials cred

// Create the credenitals with passwords and making sure it doesnt exists already
for (item in projects) {
  randomPassword = RandomStringUtils.random(randomPasswordLength, charset.toCharArray())
  credExists=findCredentials("${item}")
  if (credExists){
    println "Skipping ${item}, credential exists"
  } else {
    println "creating credentials for ${item}" 
    cred = (Credentials) new UsernamePasswordCredentialsImpl(CredentialsScope.GLOBAL,"${item}", "${item}", "${item}", "${randomPassword}")
    SystemCredentialsProvider.getInstance().getStore().addCredentials(Domain.global(), cred)
  }
}

