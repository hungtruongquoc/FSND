/* Replace with variables from Auth0 configuration
 * ensure all variables on this page match your project
 */

export const environment = {
  production: false,
  apiServerUrl: 'http://127.0.0.1:5000/api', // the running FLASK api server url
  auth0: {
    url: 'dev-gfdym553', // the auth0 domain prefix
    audience: 'coffee_fsnd', // the audience set for the auth0 app
    clientId: 'QU0Zkv2iRmh4JhJYQcT1d5Fqf7k6Evj1', // the client id generated for the auth0 app
    callbackURL: 'http://localhost:4200', // the base url of the running ionic application.
  }
};
