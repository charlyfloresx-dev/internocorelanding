using Interno.DJO.Helpers;

namespace Interno.DJO.Services
{
    public interface IPrinterService
    {
        void Send(string ipAddress, string port, string ZPLString);
    }
    public class EmailService : IPrinterService
    {
        /*
        string ZPLString =
        "^XA" +
        "^FO50,50" +
        "^A0N50,50" +
        "^FDHello, World!^FS" +
        "^XZ";
        */
        public void Send(string ipAddress, int port, string ZPLString)
        {
            try
            {
                // Open connection
                System.Net.Sockets.TcpClient client = new System.Net.Sockets.TcpClient();
                client.Connect(ipAddress, port);

                // Write ZPL String to connection
                System.IO.StreamWriter writer = new System.IO.StreamWriter(client.GetStream());
                writer.Write(ZPLString);
                writer.Flush();

                // Close Connection
                writer.Close();
                client.Close();
            }
            catch (Exception ex)
            {
                // Catch Exception
            }
        }
    }
}