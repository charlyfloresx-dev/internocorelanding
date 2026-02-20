using System.Net;
using System.IO;

using Microsoft.Extensions.Options;
using MimeKit;
using MimeKit.Text;
using MailKit.Net.Smtp;
using MailKit.Security;

using Interno.Domain.Helpers;

namespace Interno.Domain.Services
{
    public interface IEmailService
    {
        void Send(string from, string to, string Subject, string html);
        void SendNotif(string to, string Subject, IEmailBody html);
    }
    public class EmailService : IEmailService
    {
        private readonly AppSettings _appSettings;
        public EmailService(IOptions<AppSettings> appSettings)
        {
            _appSettings = appSettings.Value;
        }

        public void Send(string from, string to, string subject, string html)
        {
            var email = new MimeMessage();
            email.From.Add(MailboxAddress.Parse(from));
            email.To.Add(MailboxAddress.Parse(to));
            email.Subject = subject;
            email.Body = new TextPart(TextFormat.Html) { Text = html };
            // send email
            var smtp = new SmtpClient();
            smtp.Connect(_appSettings.SmtpHost, _appSettings.SmtpPort, SecureSocketOptions.Auto);
            smtp.Authenticate(_appSettings.SmtpUser, _appSettings.SmtpPass);
            smtp.Send(email);
            smtp.Disconnect(true);
        }

        public void SendNotif(string to, string subject, IEmailBody body)
        {
            Stream stream = new WebClient().OpenRead("https://sdcscansys1.djoglobal.com/cf-enovis/mail.html");

            using (StreamReader reader = new StreamReader(stream))
            {
                string html = reader.ReadToEnd();
                //Creamos Email
                var email = new MimeMessage();
                email.From.Add(MailboxAddress.Parse("TJMNotifications@djoglobal.com"));
                email.To.Add(MailboxAddress.Parse(to));
                email.Subject = subject;
                var html2 = html.Replace("{{title}}", "<b>" + body.Title + "</b>").Replace("{{description}}", body.Body).Replace("{{linkTittle}}", body.LinkTitle).Replace("{{link}}", body.Link);
                //Console.WriteLine(html2);
                email.Body = new TextPart(TextFormat.Html) { Text = html2 };
                // send email
                var smtp = new SmtpClient();
                smtp.Connect(_appSettings.SmtpHost, _appSettings.SmtpPort, SecureSocketOptions.Auto);
                smtp.Authenticate(_appSettings.SmtpUser, _appSettings.SmtpPass);
                smtp.Send(email);
                smtp.Disconnect(true);
            }
        }
    }

    public class IEmailBody
    {
        public string Title { get; set; }
        public string Body { get; set; }
        public string Employee { get; set; }
        public string LinkTitle { get; set; }
        public string Link { get; set; }
    }
}