using System;
using System.Net.Sockets;
using System.Text;
using Interno.Domain.Helpers;


namespace Interno.Domain.Services
{

    public class ZPLException : Exception
    {
        public ZPLException() { }
        public ZPLException(string message) : base(message) { }
    }
    public interface IPrinterService
    {
        void Send(string ipAddress, string ZPLString, int port);
    }
    public class PrinterService : IPrinterService
    {
        /*
        string ZPLString =
        "^XA" +
        "^FO50,50" +
        "^A0N50,50" +
        "^FDHello, World!^FS" +
        "^XZ";
        */
        //"10.7.51.223"
        public void Send(string ipAddress, string ZPLString, int port = 9100)
        {
            try
            {
                using (TcpClient client = new TcpClient(ipAddress, port))
                using (NetworkStream stream = client.GetStream())
                {
                    // Convierte el código ZPL en bytes y envíalo al socket de la impresora
                    byte[] zplBytes = Encoding.UTF8.GetBytes(ZPLString);
                    stream.Write(zplBytes, 0, zplBytes.Length);
                }
                Console.WriteLine("Código ZPL enviado e impreso con éxito en " + ipAddress);
            }
            catch (Exception ex)
            {
                new ZPLException("ZPL Error: " + ex.Message);
            }
        }
    }
}